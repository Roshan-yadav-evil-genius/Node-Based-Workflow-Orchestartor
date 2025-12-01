"""
Loop Manager for Production Mode loop execution.

This module handles execution of a single loop in Production Mode, managing
the producer -> blocking -> non-blocking execution flow following the
Single Responsibility Principle.
"""

import asyncio
from typing import Optional

from domain import ExecutionPool, NodeData
from dlq import DLQManager
from executor import Executor
from pool_selector import PoolSelector
from queue_manager import QueueManager
from workflow_loader import WorkflowGraph


class LoopManager:
    """
    Manages execution of a single loop in Production Mode.
    
    Executes the loop cycle: Producer -> Blocking Nodes -> Non-Blocking Node,
    then returns to Producer for the next iteration. Handles errors by routing
    to DLQ and immediately returning control to Producer.
    """
    
    def __init__(
        self,
        producer_id: str,
        workflow_graph: WorkflowGraph,
        queue_manager: QueueManager,
        dlq_manager: DLQManager,
        executor: Optional[Executor] = None
    ):
        """
        Initialize LoopManager.
        
        Args:
            producer_id: ID of the producer node that starts this loop
            workflow_graph: WorkflowGraph containing all nodes
            queue_manager: QueueManager for cross-loop communication
            dlq_manager: DLQManager for error handling
            executor: Optional Executor instance (creates new one if not provided)
        """
        self._producer_id = producer_id
        self._workflow_graph = workflow_graph
        self._queue_manager = queue_manager
        self._dlq_manager = dlq_manager
        self._executor = executor or Executor()
        self._pool_selector = PoolSelector()
        
        self._running = False
        self._stop_event = asyncio.Event()
        self._execution_pool: Optional[ExecutionPool] = None
    
    async def run_loop(self) -> None:
        """
        Main loop execution method.
        
        Runs the loop continuously until stopped. Each iteration:
        1. Executes producer node
        2. Sequentially executes all blocking nodes
        3. Executes non-blocking node (iteration end)
        4. Returns to producer for next iteration
        
        The loop runs in the execution pool determined by node preferences.
        """
        self._running = True
        self._stop_event.clear()
        
        # Determine execution pool for this loop
        self._execution_pool = self._pool_selector.select_pool_for_loop(
            self._producer_id,
            self._workflow_graph
        )
        
        # Main loop
        while self._running and not self._stop_event.is_set():
            try:
                # Use dynamic routing (None means use dynamic traversal)
                await self._execute_iteration(None)
            except asyncio.CancelledError:
                # Loop was cancelled
                break
            except Exception as e:
                # Unexpected error in loop management - log and continue
                # In production, you might want to stop the loop or alert
                print(f"Unexpected error in loop '{self._producer_id}': {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _execute_iteration(self, node_chain: list[str]) -> None:
        """
        Execute one iteration of the loop.
        
        Supports both static chains (for simple workflows) and dynamic routing
        (for conditional nodes). If node_chain is provided, uses it. Otherwise,
        dynamically traverses the graph handling conditional routing.
        
        Args:
            node_chain: Optional ordered list of node IDs (if None, uses dynamic routing)
        """
        node_data = NodeData()  # Start with empty data
        current_node_id = self._producer_id
        
        # Track visited nodes to prevent infinite loops
        visited = set()
        
        while current_node_id:
            # Prevent infinite loops
            if current_node_id in visited:
                break
            visited.add(current_node_id)
            
            try:
                # Execute current node
                node_data = await self._execute_node(current_node_id, node_data)
                
                # Check if current node is non-blocking (iteration end)
                current_node = self._workflow_graph.get_node(current_node_id)
                if current_node and hasattr(current_node, 'node_config'):
                    node_type = current_node.node_config.node_type.lower()
                    if node_type in ['non-blocking', 'nonblocking', 'queue', 'queue-node-dummy', 
                                     'store-node', 'db-node', 'telegram-sender', 'db-status-updater', 
                                     'playwright-freelance-bidder', 'llm-proposal-preparer']:
                        # Iteration ends at non-blocking node
                        break
                
                # Get next node (handles conditional routing)
                next_node_id = self._workflow_graph.get_next_node(current_node_id, node_data)
                current_node_id = next_node_id
                
            except Exception as e:
                # Handle node error: send to DLQ and return to producer
                await self._handle_node_error(current_node_id, node_data, e)
                # Return to producer for next iteration
                return
    
    async def _execute_node(self, node_id: str, node_data: NodeData) -> NodeData:
        """
        Execute a single node.
        
        Args:
            node_id: ID of the node to execute
            node_data: Input data for the node
            
        Returns:
            NodeData: Output data from the node
            
        Raises:
            Exception: Any exception raised by the node
        """
        node = self._workflow_graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Node '{node_id}' not found")
        
        # Execute node in its preferred pool (or loop's pool)
        # For Production Mode, we use the loop's selected pool
        return await self._executor.execute_in_pool(
            self._execution_pool,
            node,
            node_data
        )
    
    async def _handle_node_error(
        self,
        node_id: str,
        node_data: NodeData,
        error: Exception
    ) -> None:
        """
        Handle node execution error.
        
        Implements fail-fast policy: send to DLQ and immediately return
        control to producer (no retries).
        
        Args:
            node_id: ID of the failed node
            node_data: The payload that failed
            error: The exception that was raised
        """
        await self._dlq_manager.send_to_dlq(node_id, node_data, error)
        # Control immediately returns to producer (handled in _execute_iteration)
    
    def stop(self) -> None:
        """Stop the loop execution."""
        self._running = False
        self._stop_event.set()
    
    def is_running(self) -> bool:
        """Check if the loop is currently running."""
        return self._running
    
    def get_execution_pool(self) -> Optional[ExecutionPool]:
        """Get the execution pool selected for this loop."""
        return self._execution_pool
