"""
LoopManager - Production Mode Execution Engine

MULTIPLE BRANCH SUPPORT:
========================
This module implements the execution logic for workflows with multiple branches.
The key architectural change is handling Dict[str, List[WorkflowNode]] instead of
Dict[str, WorkflowNode] in the WorkflowNode.next field.

EXECUTION FLOW:
===============
1. Producer executes and generates data
2. Traverse graph until NonBlockingNode is reached
3. For each node, check if it's LogicalNode or regular node:
   - LogicalNode: Select ONE branch based on output ("yes" or "no")
   - Regular node: Execute ALL branches in list sequentially
4. NonBlockingNode stops iteration and returns to producer

MULTIPLE BRANCH BEHAVIOR:
=========================
- Logical nodes: Select first node from list for chosen branch key
- Non-logical nodes: Execute ALL nodes in list sequentially
- Each branch receives same input data from parent
- All branches execute regardless of NonBlockingNode type
- Example: workflow1.json - node "1" executes both node "10" and node "14"
"""

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
    
    ARCHITECTURE:
    - Each LoopManager manages one ProducerNode and its execution chain
    - Executes continuously: Producer → Blocking Nodes → NonBlockingNode → repeat
    - Handles multiple branches by executing all nodes in list sequentially
    
    MULTIPLE BRANCH SUPPORT:
    - WorkflowNode.next is now Dict[str, List[WorkflowNode]]
    - Logical nodes: Select one branch from list based on output
    - Non-logical nodes: Execute all branches in list sequentially
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
                
                # ====================================================================
                # TRAVERSAL LOGIC: Handles Logical vs Non-Logical Nodes
                # ====================================================================
                # This loop traverses the graph from producer until NonBlockingNode.
                # Key decision point: Is current node a LogicalNode?
                # - LogicalNode: Select ONE branch based on output ("yes" or "no")
                # - Regular node: Execute ALL branches in list sequentially
                # ====================================================================
                
                current_workflow_node = self.producer_workflow_node
                while True:
                    # Get next nodes dictionary: Dict[str, List[WorkflowNode]]
                    # Key examples: "default", "yes", "no"
                    # Value: List of WorkflowNodes (supports multiple branches per key)
                    next_nodes = current_workflow_node.next
                    
                    if not next_nodes:
                        break  # No more nodes - end of chain
                    
                    # DECISION POINT: Check if current node is LogicalNode
                    # Logical nodes (e.g., if-condition) select ONE branch
                    # Regular nodes execute ALL branches
                    current_node = current_workflow_node.instance
                    branch_key = None
                    
                    # ====================================================================
                    # LOGICAL NODE HANDLING: Select ONE Branch
                    # ====================================================================
                    # Logical nodes (e.g., if-condition) have conditional output
                    # They select ONE branch based on their output property ("yes" or "no")
                    # Even if multiple nodes exist in the list, only first is selected
                    # ====================================================================
                    if isinstance(current_node, LogicalNode):
                        # Get branch key from LogicalNode output ("yes" or "no")
                        # This is set by the LogicalNode during its execute() method
                        branch_key = current_node.output  # "yes" or "no"
                        
                        if branch_key and branch_key in next_nodes:
                            # Get list for selected branch key
                            # MULTIPLE BRANCH SUPPORT: Even though list may have multiple nodes,
                            # LogicalNode selects only the FIRST node (maintains backward compatibility)
                            next_nodes_list = next_nodes[branch_key]
                            next_workflow_node = next_nodes_list[0] if next_nodes_list else None
                            logger.info(f"Selected branch",branch_key=branch_key,next_workflow_node=next_workflow_node.id if next_workflow_node else None, available_branches=next_nodes.keys())
                        else:
                            # Fallback: If branch key not found or not set, use default or first available
                            logger.info(f"No branch selected, falling back to default or first available", available_branches=next_nodes.keys())
                            default_list = next_nodes.get("default", [])
                            first_key = list(next_nodes.keys())[0] if next_nodes else None
                            first_list = next_nodes.get(first_key, []) if first_key else []
                            next_workflow_node = (default_list[0] if default_list else None) or (first_list[0] if first_list else None)
                            logger.info(f"Selected default or first available",next_workflow_node=next_workflow_node.id if next_workflow_node else None, available_branches=next_nodes.keys())

                        # For LogicalNode, execute only the selected branch (single node)
                        if not next_workflow_node:
                            break
                        
                        # Execute the selected branch node
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
                        
                        # NonBlockingNode check: Stops traversal in single chain
                        # For LogicalNode, this applies to the selected branch only
                        if isinstance(next_node_instance, NonBlockingNode):
                            break
                        
                        # Move to next workflow node in the selected branch
                        current_workflow_node = next_workflow_node

                    else:
                        # ====================================================================
                        # NON-LOGICAL NODE HANDLING: Execute ALL Branches Sequentially
                        # ====================================================================
                        # Regular nodes (Producer, Blocking, NonBlocking) execute ALL branches
                        # in the list sequentially. This is the key feature for multiple branch support.
                        # Example: workflow1.json - node "1" executes both node "10" and node "14"
                        # ====================================================================
                        
                        # BRANCH KEY SELECTION: Prioritize "default" key, fallback to first available
                        # This handles cases where multiple branch keys exist
                        branch_key = "default" if "default" in next_nodes else list(next_nodes.keys())[0] if next_nodes else None
                        
                        if not branch_key:
                            break
                        
                        # Get the list of nodes for the selected branch key
                        # This list may contain one or multiple nodes
                        next_nodes_list = next_nodes[branch_key]
                        
                        # ====================================================================
                        # SINGLE BRANCH CASE: Backward Compatible Behavior
                        # ====================================================================
                        # When list has only one node, execute normally (like old single-node structure)
                        # This maintains backward compatibility with existing workflows
                        # ====================================================================
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
                            
                            # NonBlockingNode check: Stops traversal in single chain
                            if isinstance(next_node_instance, NonBlockingNode):
                                break
                            
                            # Move to next workflow node in the chain
                            current_workflow_node = next_workflow_node
                            
                        # ====================================================================
                        # MULTIPLE BRANCH CASE: Sequential Execution
                        # ====================================================================
                        # When list has multiple nodes, execute ALL of them sequentially
                        # This is the key feature that enables multiple branch support
                        # Example: workflow1.json - node "1" has [node_10, node_14]
                        #          Both nodes execute sequentially, one after another
                        # ====================================================================
                        else:
                            logger.info(
                                f"Executing Multiple Branches Sequentially",
                                loop_id=self.loop_identifier,
                                branch_count=len(next_nodes_list),
                                branch_key=branch_key,
                                loop_count=self.loop_count,
                            )
                            
                            # EXECUTE ALL BRANCHES SEQUENTIALLY
                            # Each branch receives the same input data from parent node
                            # Branches execute one after another (not concurrently)
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
                                
                                # IMPORTANT: All branches receive the SAME input data
                                # Each branch gets the output from the parent node
                                # This ensures consistent data flow across all branches
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
                                
                                # CRITICAL: For multiple branches, we execute ALL branches
                                # regardless of NonBlockingNode type. This ensures that
                                # all branches complete execution (e.g., both node 10 and
                                # node 14 in workflow1.json execute even though they're
                                # both NonBlockingNodes).
                                # The NonBlockingNode check only applies when continuing
                                # traversal in a single chain, not when executing multiple
                                # parallel branches.
                            
                            # After executing all branches, we can't continue to a single next node
                            # because each branch would continue independently. For simplicity,
                            # we break here and return to the producer for the next iteration.
                            # This design ensures all branches complete before starting next cycle.
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
