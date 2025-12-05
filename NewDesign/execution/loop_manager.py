import asyncio
import structlog
from typing import Optional
from Nodes.Core.BaseNode import ProducerNode, NonBlockingNode, LogicalNode
from Nodes.Core.Data import NodeOutput
from core.utils import node_type
from core.workflow_node import WorkflowNode
from execution.executor import Executor

logger = structlog.get_logger(__name__)


class LoopManager:
    """
    Manages a single loop in Production Mode.
    Executes node chains in defined order.
    """

    def __init__(
        self,
        producer_workflow_node: WorkflowNode,
        executor: Optional[Executor] = None,
    ):
        self.producer_workflow_node = producer_workflow_node
        self.producer = producer_workflow_node.instance  # For backward compatibility in logging/execution
        self.executor = executor or Executor()
        self.running = False
        self.loop_count = 0
        self.loop_identifier = self.producer_workflow_node.id

    async def start(self):
        self.running = True

        while self.running:
            self.loop_count += 1
            try:
                # Execute producer
                producer = self.producer_workflow_node.instance
                logger.info(
                    f"Executing Producer",
                    loop_id=self.loop_identifier,
                    node_id=producer.config.id,
                    node_type=f"{node_type(producer)}({producer.identifier()})",
                    loop_count=self.loop_count,
                )
                data = await self.executor.execute_in_pool(
                    producer.execution_pool, producer, NodeOutput(data={})
                )
                logger.info(
                    f"Producer Executed",
                    loop_id=self.loop_identifier,
                    node_id=producer.config.id,
                    output=data,
                    node_type=f"{node_type(producer)}({producer.identifier()})",
                    loop_count=self.loop_count,
                )
                
                # Traverse dynamically until NonBlockingNode
                current_workflow_node = self.producer_workflow_node
                while True:
                    # Get next nodes
                    next_nodes = current_workflow_node.next
                    
                    if not next_nodes:
                        break  # No more nodes
                    
                    # Check if current node is LogicalNode and get branch key
                    current_node = current_workflow_node.instance
                    branch_key = None
                    
                    if isinstance(current_node, LogicalNode):
                        branch_key = current_node.output  # "yes" or "no"
                        if branch_key and branch_key in next_nodes:
                            # Get list for selected branch key and select first node
                            next_nodes_list = next_nodes[branch_key]
                            next_workflow_node = next_nodes_list[0] if next_nodes_list else None
                            logger.info(f"Selected branch",branch_key=branch_key,next_workflow_node=next_workflow_node.id if next_workflow_node else None, available_branches=next_nodes.keys())
                        else:
                            logger.info(f"No branch selected, falling back to default or first available", available_branches=next_nodes.keys())
                            # Fallback to default or first available
                            default_list = next_nodes.get("default", [])
                            first_key = list(next_nodes.keys())[0] if next_nodes else None
                            first_list = next_nodes.get(first_key, []) if first_key else []
                            next_workflow_node = (default_list[0] if default_list else None) or (first_list[0] if first_list else None)
                            logger.info(f"Selected default or first available",next_workflow_node=next_workflow_node.id if next_workflow_node else None, available_branches=next_nodes.keys())

                        # For LogicalNode, execute only the selected branch
                        if not next_workflow_node:
                            break
                        
                        # Execute next node
                        next_node_instance = next_workflow_node.instance
                        logger.info(
                            f"Executing Node",
                            loop_id=self.loop_identifier,
                            node_id=next_node_instance.config.id,
                            node_type=f"{node_type(next_node_instance)}({next_node_instance.identifier()})",
                            input=data,
                            loop_count=self.loop_count,
                            branch_key=branch_key if branch_key else "default",
                        )
                        data = await self.executor.execute_in_pool(
                            next_node_instance.execution_pool, next_node_instance, data
                        )
                        logger.info(
                            f"Node Executed",
                            loop_id=self.loop_identifier,
                            node_id=next_node_instance.config.id,
                            output=data,
                            node_type=f"{node_type(next_node_instance)}({next_node_instance.identifier()})",
                        )
                        
                        # Check if NonBlockingNode - if so, iteration ends
                        if isinstance(next_node_instance, NonBlockingNode):
                            break
                        
                        # Move to next workflow node
                        current_workflow_node = next_workflow_node

                    else:
                        # Non-logical: execute ALL branches sequentially
                        # Get the default key (or first available key)
                        branch_key = "default" if "default" in next_nodes else list(next_nodes.keys())[0] if next_nodes else None
                        
                        if not branch_key:
                            break
                        
                        next_nodes_list = next_nodes[branch_key]
                        
                        if len(next_nodes_list) == 1:
                            # Single branch - execute normally
                            next_workflow_node = next_nodes_list[0]
                            next_node_instance = next_workflow_node.instance
                            logger.info(
                                f"Executing Node",
                                loop_id=self.loop_identifier,
                                node_id=next_node_instance.config.id,
                                node_type=f"{node_type(next_node_instance)}({next_node_instance.identifier()})",
                                input=data,
                                loop_count=self.loop_count,
                                branch_key=branch_key,
                            )
                            data = await self.executor.execute_in_pool(
                                next_node_instance.execution_pool, next_node_instance, data
                            )
                            logger.info(
                                f"Node Executed",
                                loop_id=self.loop_identifier,
                                node_id=next_node_instance.config.id,
                                output=data,
                                node_type=f"{node_type(next_node_instance)}({next_node_instance.identifier()})",
                            )
                            
                            # Check if NonBlockingNode - if so, iteration ends
                            if isinstance(next_node_instance, NonBlockingNode):
                                break
                            
                            # Move to next workflow node
                            current_workflow_node = next_workflow_node
                        else:
                            # Multiple branches - execute sequentially
                            logger.info(
                                f"Executing Multiple Branches Sequentially",
                                loop_id=self.loop_identifier,
                                branch_count=len(next_nodes_list),
                                branch_key=branch_key,
                                loop_count=self.loop_count,
                            )
                            
                            # Execute each branch sequentially
                            for idx, next_workflow_node in enumerate(next_nodes_list):
                                next_node_instance = next_workflow_node.instance
                                logger.info(
                                    f"Executing Branch",
                                    loop_id=self.loop_identifier,
                                    node_id=next_node_instance.config.id,
                                    branch_index=idx + 1,
                                    total_branches=len(next_nodes_list),
                                    branch_key=branch_key,
                                    loop_count=self.loop_count,
                                )
                                
                                # Use the same data for all branches (each branch gets the same input)
                                branch_data = await self.executor.execute_in_pool(
                                    next_node_instance.execution_pool, next_node_instance, data
                                )
                                
                                logger.info(
                                    f"Branch Executed",
                                    loop_id=self.loop_identifier,
                                    node_id=next_node_instance.config.id,
                                    branch_index=idx + 1,
                                    output=branch_data,
                                    branch_key=branch_key,
                                    loop_count=self.loop_count,
                                )
                                
                                # Note: For multiple branches, we execute ALL branches regardless of NonBlockingNode
                                # The NonBlockingNode check only applies when continuing traversal in a single chain
                            
                            # After executing all branches, we can't continue to a single next node
                            # Each branch would continue independently, but for simplicity, we break here
                            # You may want to handle this differently based on your requirements
                            break

            except Exception as e:
                logger.exception("Error in loop", error=str(e))
                # In real impl, send to DLQ
                await asyncio.sleep(1)  # Prevent tight loop on error

    def stop(self):
        self.running = False

    def shutdown(self):
        """Shutdown executor pools when loop stops."""
        self.executor.shutdown()
