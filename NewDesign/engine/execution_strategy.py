"""
Execution Strategy pattern for pluggable execution models.
Single Responsibility: Abstract execution model interface and implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
import functools


class ExecutionStrategy(ABC):
    """
    Abstract base class for execution strategies.
    Defines the interface for executing nodes and chains.
    """

    @abstractmethod
    async def execute_node(self, node: Any, data: Any = None) -> Any:
        """
        Execute a single node asynchronously.
        
        Args:
            node: Node to execute
            data: Input data for the node
            
        Returns:
            Output from the node
        """
        pass

    @abstractmethod
    async def execute_chain(
        self,
        nodes: List[Any],
        data: Any,
        get_next_nodes: Callable[[Any, Any], List[Any]]
    ) -> Any:
        """
        Execute a chain of nodes sequentially.
        
        Args:
            nodes: List of nodes to execute
            data: Initial input data
            get_next_nodes: Function to get next nodes based on current node and output
            
        Returns:
            Final output from the chain
        """
        pass


class AsyncExecutionStrategy(ExecutionStrategy):
    """
    Execution strategy using asyncio for async/await execution.
    Runs synchronous node code in the event loop.
    """

    def __init__(self):
        """Initialize async execution strategy."""
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def execute_node(self, node: Any, data: Any = None) -> Any:
        """
        Execute a node using asyncio.
        
        Args:
            node: Node to execute
            data: Input data for the node
            
        Returns:
            Output from the node
        """
        # Run synchronous node.run() in the event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, node.run, data)

    async def execute_chain(
        self,
        nodes: List[Any],
        data: Any,
        get_next_nodes: Callable[[Any, Any], List[Any]]
    ) -> Any:
        """
        Execute a chain of nodes sequentially using asyncio.
        
        Args:
            nodes: List of nodes to execute
            data: Initial input data
            get_next_nodes: Function to get next nodes based on current node and output
            
        Returns:
            Final output from the chain
        """
        current_data = data
        for node in nodes:
            current_data = await self.execute_node(node, current_data)
            # Get next nodes based on current node and output
            next_nodes = get_next_nodes(node, current_data)
            if next_nodes:
                # Recursively execute next nodes
                current_data = await self.execute_chain(
                    next_nodes, current_data, get_next_nodes
                )
        return current_data


class ThreadExecutionStrategy(ExecutionStrategy):
    """
    Execution strategy using ThreadPoolExecutor for thread-based execution.
    """

    def __init__(self, max_workers: int = 8):
        """
        Initialize thread execution strategy.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def execute_node(self, node: Any, data: Any = None) -> Any:
        """
        Execute a node using thread pool.
        
        Args:
            node: Node to execute
            data: Input data for the node
            
        Returns:
            Output from the node
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, node.run, data)

    async def execute_chain(
        self,
        nodes: List[Any],
        data: Any,
        get_next_nodes: Callable[[Any, Any], List[Any]]
    ) -> Any:
        """
        Execute a chain of nodes sequentially using thread pool.
        
        Args:
            nodes: List of nodes to execute
            data: Initial input data
            get_next_nodes: Function to get next nodes based on current node and output
            
        Returns:
            Final output from the chain
        """
        current_data = data
        for node in nodes:
            current_data = await self.execute_node(node, current_data)
            # Get next nodes based on current node and output
            next_nodes = get_next_nodes(node, current_data)
            if next_nodes:
                # Recursively execute next nodes
                current_data = await self.execute_chain(
                    next_nodes, current_data, get_next_nodes
                )
        return current_data

    def shutdown(self) -> None:
        """Shutdown the thread pool executor."""
        self._executor.shutdown(wait=True)


class ProcessExecutionStrategy(ExecutionStrategy):
    """
    Execution strategy using ProcessPoolExecutor for process-based execution.
    Note: Nodes must be picklable for process execution.
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize process execution strategy.
        
        Args:
            max_workers: Maximum number of worker processes
        """
        self._executor = ProcessPoolExecutor(max_workers=max_workers)

    async def execute_node(self, node: Any, data: Any = None) -> Any:
        """
        Execute a node using process pool.
        
        Args:
            node: Node to execute (must be picklable)
            data: Input data for the node (must be picklable)
            
        Returns:
            Output from the node
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, node.run, data)

    async def execute_chain(
        self,
        nodes: List[Any],
        data: Any,
        get_next_nodes: Callable[[Any, Any], List[Any]]
    ) -> Any:
        """
        Execute a chain of nodes sequentially using process pool.
        
        Args:
            nodes: List of nodes to execute (must be picklable)
            data: Initial input data (must be picklable)
            get_next_nodes: Function to get next nodes based on current node and output
            
        Returns:
            Final output from the chain
        """
        current_data = data
        for node in nodes:
            current_data = await self.execute_node(node, current_data)
            # Get next nodes based on current node and output
            next_nodes = get_next_nodes(node, current_data)
            if next_nodes:
                # Recursively execute next nodes
                current_data = await self.execute_chain(
                    next_nodes, current_data, get_next_nodes
                )
        return current_data

    def shutdown(self) -> None:
        """Shutdown the process pool executor."""
        self._executor.shutdown(wait=True)

