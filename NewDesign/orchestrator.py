"""
Workflow Orchestrator - Main coordinator for workflow execution.

This module provides the Orchestrator class that manages workflows in both
Production Mode (using LoopManagers) and Development Mode (direct node execution),
following the Single Responsibility Principle.
"""

import asyncio
from typing import Dict, List, Optional

from cache_manager import CacheManager
from dlq import DLQManager
from domain import NodeData
from executor import Executor
from loop_manager import LoopManager
from queue_manager import QueueManager
from workflow_loader import WorkflowGraph, WorkflowLoader


class Orchestrator:
    """
    Main coordinator for workflow execution in both Production and Development modes.
    
    Responsibilities:
    - Workflow loading and graph management
    - Production Mode: LoopManager lifecycle management
    - Development Mode: Direct node execution with dependency resolution
    - State management and observability
    - Queue and cache management
    """
    
    def __init__(self, mode: str, redis_client):
        """
        Initialize Orchestrator.
        
        Args:
            mode: Operating mode - "production" or "development"
            redis_client: Redis client instance (must support async operations)
            
        Raises:
            ValueError: If mode is not "production" or "development"
        """
        if mode not in ["production", "development"]:
            raise ValueError(f"Mode must be 'production' or 'development', got '{mode}'")
        
        self._mode = mode
        self._redis = redis_client
        
        # Initialize managers
        self.queue_manager = QueueManager(redis_client)
        self.cache_manager = CacheManager(redis_client)
        self.dlq_manager = DLQManager(redis_client)
        self._executor = Executor()
        
        # Workflow state
        self.workflow_graph: Optional[WorkflowGraph] = None
        self._workflow_loader = WorkflowLoader(queue_manager=self.queue_manager)
        
        # Production Mode state
        self._loop_managers: Dict[str, LoopManager] = {}
        self._loop_tasks: Dict[str, asyncio.Task] = {}
    
    @property
    def mode(self) -> str:
        """Get the current operating mode."""
        return self._mode
    
    # ==================== Workflow Loading ====================
    
    async def load_workflow(self, json_data: Dict) -> None:
        """
        Load and initialize workflow from React Flow JSON.
        
        Args:
            json_data: React Flow JSON dictionary
            
        Raises:
            ValueError: If workflow JSON is invalid
        """
        self.workflow_graph = self._workflow_loader.load_from_json(json_data)
    
    # ==================== Production Mode Methods ====================
    
    async def start_loop(self, producer_id: str) -> None:
        """
        Start a loop manager for a producer node (Production Mode only).
        
        Args:
            producer_id: ID of the producer node that starts the loop
            
        Raises:
            RuntimeError: If not in Production Mode or workflow not loaded
            ValueError: If producer_id is invalid
        """
        if self._mode != "production":
            raise RuntimeError("start_loop() is only available in Production Mode")
        
        if self.workflow_graph is None:
            raise RuntimeError("Workflow must be loaded before starting loops")
        
        if producer_id not in self.workflow_graph.nodes:
            raise ValueError(f"Producer node '{producer_id}' not found in workflow")
        
        if producer_id in self._loop_managers:
            raise ValueError(f"Loop for producer '{producer_id}' is already running")
        
        # Create LoopManager
        loop_manager = LoopManager(
            producer_id=producer_id,
            workflow_graph=self.workflow_graph,
            queue_manager=self.queue_manager,
            dlq_manager=self.dlq_manager,
            executor=self._executor
        )
        
        self._loop_managers[producer_id] = loop_manager
        
        # Start loop in background task
        task = asyncio.create_task(loop_manager.run_loop())
        self._loop_tasks[producer_id] = task
    
    async def stop_loop(self, producer_id: str) -> None:
        """
        Stop a running loop manager (Production Mode only).
        
        Args:
            producer_id: ID of the producer node
            
        Raises:
            RuntimeError: If not in Production Mode
            ValueError: If loop is not running
        """
        if self._mode != "production":
            raise RuntimeError("stop_loop() is only available in Production Mode")
        
        if producer_id not in self._loop_managers:
            raise ValueError(f"Loop for producer '{producer_id}' is not running")
        
        # Stop the loop manager
        loop_manager = self._loop_managers[producer_id]
        loop_manager.stop()
        
        # Cancel the task
        task = self._loop_tasks.get(producer_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Clean up
        del self._loop_managers[producer_id]
        if producer_id in self._loop_tasks:
            del self._loop_tasks[producer_id]
    
    async def start_all_loops(self) -> None:
        """
        Start all loops in the workflow (Production Mode only).
        
        Finds all producer nodes and starts a loop manager for each.
        
        Raises:
            RuntimeError: If not in Production Mode or workflow not loaded
        """
        if self._mode != "production":
            raise RuntimeError("start_all_loops() is only available in Production Mode")
        
        if self.workflow_graph is None:
            raise RuntimeError("Workflow must be loaded before starting loops")
        
        producer_nodes = self.workflow_graph.get_producer_nodes()
        
        for producer_id in producer_nodes:
            try:
                await self.start_loop(producer_id)
            except ValueError as e:
                # Skip if already running
                if "already running" not in str(e):
                    raise
    
    async def stop_all_loops(self) -> None:
        """
        Stop all running loops (Production Mode only).
        
        Raises:
            RuntimeError: If not in Production Mode
        """
        if self._mode != "production":
            raise RuntimeError("stop_all_loops() is only available in Production Mode")
        
        producer_ids = list(self._loop_managers.keys())
        for producer_id in producer_ids:
            await self.stop_loop(producer_id)
    
    def get_running_loops(self) -> List[str]:
        """
        Get list of currently running loop producer IDs.
        
        Returns:
            List[str]: List of producer node IDs with running loops
        """
        return list(self._loop_managers.keys())
    
    # ==================== Development Mode Methods ====================
    
    async def execute_node(self, node_id: str, input_data: Optional[NodeData] = None) -> NodeData:
        """
        Execute a single node (Development Mode only).
        
        Execution flow:
        1. Check upstream dependencies
        2. Resolve inputs from cache (or use provided input_data)
        3. Execute node in its preferred pool
        4. Store output in cache
        
        Args:
            node_id: ID of the node to execute
            input_data: Optional input data (if not provided, resolves from cache)
            
        Returns:
            NodeData: Output data from the node execution
            
        Raises:
            RuntimeError: If not in Development Mode or workflow not loaded
            ValueError: If node_id is invalid or dependencies are missing
        """
        if self._mode != "development":
            raise RuntimeError("execute_node() is only available in Development Mode")
        
        if self.workflow_graph is None:
            raise RuntimeError("Workflow must be loaded before executing nodes")
        
        if node_id not in self.workflow_graph.nodes:
            raise ValueError(f"Node '{node_id}' not found in workflow")
        
        node = self.workflow_graph.get_node(node_id)
        if node is None:
            raise ValueError(f"Node '{node_id}' not found")
        
        # Resolve input data
        if input_data is None:
            input_data = await self._resolve_node_input(node_id)
        
        # Execute node in its preferred pool
        output_data = await self._executor.execute_in_pool(
            node.execution_pool,
            node,
            input_data
        )
        
        # Store output in cache
        await self.cache_manager.set_node_output(node_id, output_data)
        
        return output_data
    
    async def _resolve_node_input(self, node_id: str) -> NodeData:
        """
        Resolve input data for a node from upstream dependencies.
        
        Args:
            node_id: ID of the node
            
        Returns:
            NodeData: Resolved input data
            
        Raises:
            ValueError: If required dependencies are missing from cache
        """
        upstream_nodes = self.workflow_graph.get_upstream_nodes(node_id)
        
        if not upstream_nodes:
            # No upstream nodes - return empty data
            return NodeData()
        
        # For simplicity, use the first upstream node's output
        # In a more complex implementation, you might merge multiple upstream outputs
        upstream_id = upstream_nodes[0]
        cached_output = await self.cache_manager.get_node_output(upstream_id)
        
        if cached_output is None:
            raise ValueError(
                f"Upstream node '{upstream_id}' output not found in cache. "
                f"Execute upstream nodes first."
            )
        
        return cached_output
    
    async def clear_cache(self) -> None:
        """
        Clear all cached node outputs (Development Mode).
        
        Useful for resetting state during development.
        """
        await self.cache_manager.clear_all()
    
    # ==================== Common Methods ====================
    
    def get_workflow_graph(self) -> Optional[WorkflowGraph]:
        """Get the current workflow graph."""
        return self.workflow_graph
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator and clean up resources."""
        if self._mode == "production":
            await self.stop_all_loops()
        
        self._executor.shutdown()
