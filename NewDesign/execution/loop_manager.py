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
                            next_workflow_node = next_nodes[branch_key]
                            logger.info(f"Selected branch",branch_key=branch_key,next_workflow_node=next_workflow_node.id, available_branches=next_nodes.keys())
                        else:
                            logger.info(f"No branch selected, falling back to default or first available",next_workflow_node=next_workflow_node.id, available_branches=next_nodes.keys())
                            # Fallback to default or first available
                            next_workflow_node = next_nodes.get("default") or list(next_nodes.values())[0]
                            logger.info(f"Selected default or first available",next_workflow_node=next_workflow_node.id, available_branches=next_nodes.keys())

                    else:
                        # Non-logical: use default or first available
                        next_workflow_node = next_nodes.get("default") or list(next_nodes.values())[0]
                    
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

            except Exception as e:
                logger.exception("Error in loop", error=str(e))
                # In real impl, send to DLQ
                await asyncio.sleep(1)  # Prevent tight loop on error

    def stop(self):
        self.running = False

    def shutdown(self):
        """Shutdown executor pools when loop stops."""
        self.executor.shutdown()
