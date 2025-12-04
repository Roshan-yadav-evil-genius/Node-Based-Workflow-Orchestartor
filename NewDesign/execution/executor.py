"""
Execution pool handler for running nodes in different execution contexts.

This module provides the Executor class that handles execution of nodes
in ASYNC, THREAD, or PROCESS pools, following the Single Responsibility Principle.
"""

import asyncio
import pickle
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Optional, TYPE_CHECKING

from Nodes.Core.Data import PoolType, NodeOutput

if TYPE_CHECKING:
    from Nodes.Core.BaseNode import BaseNode


class Executor:
    """
    Executes nodes in different execution pools (async, thread, process).
    
    Handles the complexity of running async code in different execution
    contexts while maintaining proper serialization for process pools.
    """
    
    def __init__(self, max_workers_thread: int = 10, max_workers_process: int = 4):
        """
        Initialize the Executor.
        
        Args:
            max_workers_thread: Maximum number of threads in thread pool
            max_workers_process: Maximum number of processes in process pool
        """
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._process_pool: Optional[ProcessPoolExecutor] = None
        self._max_workers_thread = max_workers_thread
        self._max_workers_process = max_workers_process
    
    async def execute_in_pool(
        self,
        pool: PoolType,
        node: 'BaseNode',
        node_output: NodeOutput
    ) -> NodeOutput:
        """
        Execute a node in the specified execution pool.
        
        Args:
            pool: The execution pool type (ASYNC, THREAD, or PROCESS)
            node: The node instance to execute
            node_data: Input data for the node
            
        Returns:
            NodeData: Output data from the node execution
            
        Raises:
            Exception: Any exception raised by the node's execute method
        """
        if pool == PoolType.ASYNC:
            return await self._execute_async(node, node_output)
        elif pool == PoolType.THREAD:
            return await self._execute_thread(node, node_output)
        elif pool == PoolType.PROCESS:
            return await self._execute_process(node, node_output)
        else:
            raise ValueError(f"Unknown execution pool: {pool}")
    
    async def _execute_async(self, node: 'BaseNode', node_output: NodeOutput) -> NodeOutput:
        """Execute node directly in async context."""
        return await node.execute(node_output)
    
    @staticmethod
    def _run_in_thread(node: 'BaseNode', node_output: NodeOutput) -> NodeOutput:
        """
        Static method to execute a node in a thread pool.
        
        This method is static for consistency with _run_in_process, even though
        ThreadPoolExecutor doesn't require pickling (threads share memory).
        The nested function approach would also work, but this maintains consistency.
        """
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(node.execute(node_output))
        finally:
            new_loop.close()
    
    async def _execute_thread(self, node: 'BaseNode', node_output: NodeOutput) -> NodeOutput:
        """Execute node in thread pool."""
        if self._thread_pool is None:
            self._thread_pool = ThreadPoolExecutor(max_workers=self._max_workers_thread)
        
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            self._thread_pool,
            Executor._run_in_thread,
            node,
            node_output
        )
    
    @staticmethod
    def _run_in_process(serialized_node_bytes: bytes, serialized_data_bytes: bytes) -> bytes:
        """
        Static method to execute a node in a process pool.
        
        REASON FOR STATIC METHOD:
        This method MUST be static (not an instance method) because:
        
        1. ProcessPoolExecutor requires functions to be picklable (serializable)
        2. Nested functions (defined inside methods) that reference 'self' or instance
           methods cannot be pickled - Python's pickle module cannot serialize local
           functions that capture instance state
        3. When a nested function references 'self._deserialize_node_from_process()',
           pickle tries to serialize the entire Executor instance, which fails with:
           "Can't get local object 'Executor._execute_process.<locals>.run_in_process'"
        
        4. Static methods can be pickled because:
           - They don't depend on instance state (no 'self' parameter)
           - They don't require an instance to be called
           - They use only their parameters and standard library functions (pickle, asyncio)
        
        By making this a static method, we keep it organized within the Executor class
        while ensuring it can be safely passed to ProcessPoolExecutor.run_in_executor()
        without pickling issues.
        """
        # Deserialize in the process
        try:
            node = pickle.loads(serialized_node_bytes)
            node_data = pickle.loads(serialized_data_bytes)
        except (pickle.PickleError, AttributeError) as e:
            raise ValueError(f"Cannot deserialize in process pool: {e}") from e
        
        # Create new event loop in process
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            result = new_loop.run_until_complete(node.execute(node_data))
            return pickle.dumps(result)
        finally:
            new_loop.close()
    
    async def _execute_process(self, node: 'BaseNode', node_output: NodeOutput) -> NodeOutput:
        """Execute node in process pool."""
        if self._process_pool is None:
            self._process_pool = ProcessPoolExecutor(max_workers=self._max_workers_process)
        
        loop = asyncio.get_event_loop()
        
        # For process pool, we need to serialize the node and data
        # Note: This is a simplified approach. In practice, nodes might need
        # special handling for process pool execution due to serialization constraints.
        try:
            serialized_node = self._serialize_node_for_process(node)
            serialized_data = self._serialize_data_for_process(node_output)
        except (pickle.PickleError, AttributeError) as e:
            raise ValueError(f"Cannot serialize node for process pool: {e}") from e
        
        result_bytes = await loop.run_in_executor(
            self._process_pool,
            Executor._run_in_process,
            serialized_node,
            serialized_data
        )
        
        return self._deserialize_data_from_process(result_bytes)
    
    def _serialize_node_for_process(self, node: 'BaseNode') -> bytes:
        """Serialize node for process pool execution."""
        # Note: This is a simplified serialization. In practice, nodes with
        # non-serializable dependencies (like Redis clients) may need special handling.
        try:
            return pickle.dumps(node)
        except (pickle.PickleError, AttributeError) as e:
            raise ValueError(f"Cannot serialize node for process pool: {e}") from e
    
    def _deserialize_node_from_process(self, data: bytes) -> 'BaseNode':
        """Deserialize node from process pool."""
        try:
            return pickle.loads(data)
        except (pickle.PickleError, AttributeError) as e:
            raise ValueError(f"Cannot deserialize node from process pool: {e}") from e
    
    def _serialize_data_for_process(self, node_output: NodeOutput) -> bytes:
        """Serialize NodeData for process pool."""
        try:
            return pickle.dumps(node_output)
        except (pickle.PickleError, AttributeError) as e:
            raise ValueError(f"Cannot serialize NodeData for process pool: {e}") from e
    
    def _deserialize_data_from_process(self, data: bytes) -> NodeOutput:
        """Deserialize NodeData from process pool."""
        try:
            return pickle.loads(data)
        except (pickle.PickleError, AttributeError) as e:
            raise ValueError(f"Cannot deserialize NodeData from process pool: {e}") from e
    
    def shutdown(self) -> None:
        """Shutdown thread and process pools."""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None
        
        if self._process_pool:
            self._process_pool.shutdown(wait=True)
            self._process_pool = None
