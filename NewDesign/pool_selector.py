"""
Execution pool selector for determining loop execution pools.

This module determines the execution pool for a loop based on node preferences,
following the Single Responsibility Principle. The pool selection uses priority
ordering: PROCESS > THREAD > ASYNC.
"""

from typing import List

from domain import ExecutionPool
from workflow_loader import WorkflowGraph


class PoolSelector:
    """
    Determines execution pool for a loop based on node preferences.
    
    Inspects the ExecutionPool preference of all nodes in a chain and
    selects the highest-priority pool for the entire loop execution.
    """
    
    @staticmethod
    def select_pool(node_ids: List[str], workflow_graph: WorkflowGraph) -> ExecutionPool:
        """
        Select execution pool for a list of nodes.
        
        The pool selection algorithm:
        1. Inspect ExecutionPool preference of all nodes in the list
        2. Return the highest priority pool: PROCESS > THREAD > ASYNC
        
        Args:
            node_ids: List of node IDs in the execution chain
            workflow_graph: WorkflowGraph containing the nodes
            
        Returns:
            ExecutionPool: Selected execution pool for the loop
            
        Raises:
            ValueError: If node_ids is empty or contains invalid node IDs
        """
        if not node_ids:
            # Default to ASYNC if no nodes
            return ExecutionPool.ASYNC
        
        pools = []
        
        for node_id in node_ids:
            node = workflow_graph.get_node(node_id)
            if node is None:
                raise ValueError(f"Node '{node_id}' not found in workflow graph")
            
            pool = node.execution_pool
            pools.append(pool)
        
        # Select highest priority pool
        return ExecutionPool.highest_priority(pools)
    
    @staticmethod
    def select_pool_for_loop(producer_id: str, workflow_graph: WorkflowGraph) -> ExecutionPool:
        """
        Select execution pool for an entire loop starting from a producer.
        
        This method gets the node chain from the producer and selects
        the pool based on all nodes in that chain.
        
        Args:
            producer_id: Producer node ID that starts the loop
            workflow_graph: WorkflowGraph containing the nodes
            
        Returns:
            ExecutionPool: Selected execution pool for the loop
        """
        node_chain = workflow_graph.get_node_chain(producer_id)
        return PoolSelector.select_pool(node_chain, workflow_graph)
