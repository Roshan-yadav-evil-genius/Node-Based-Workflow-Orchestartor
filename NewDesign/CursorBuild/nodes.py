"""
Base node classes and node type implementations.

This module defines the node hierarchy following the Single Responsibility Principle.
Each node type has a clear semantic purpose in the workflow execution model.
"""

from abc import ABC, abstractmethod
from typing import Optional

from domain import ExecutionPool, NodeConfig, NodeData, NodeType


class BaseNode(ABC):
    """
    Abstract base class for all workflow nodes.
    
    All nodes must implement the async execute method and define their
    preferred execution pool. Nodes never manage their own concurrency;
    they simply run when invoked by the LoopManager or Orchestrator.
    """
    
    def __init__(self, node_config: NodeConfig):
        """
        Initialize the node with its configuration.
        
        Args:
            node_config: Static configuration for this node
        """
        self._node_config = node_config
    
    @property
    def node_config(self) -> NodeConfig:
        """Get the node's configuration."""
        return self._node_config
    
    @property
    def node_id(self) -> str:
        """Get the node's unique identifier."""
        return self._node_config.node_id
    
    @property
    def execution_pool(self) -> ExecutionPool:
        """Get the node's preferred execution pool."""
        return self._node_config.execution_pool
    
    @abstractmethod
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the node's logic.
        
        This method must be implemented by all concrete node classes.
        It should use async/await for all I/O operations and complete
        only when the node's obligations are met.
        
        Args:
            node_data: Runtime payload data for this execution
            
        Returns:
            NodeData: Transformed output data
            
        Raises:
            Exception: Any exception raised during execution will be
                      caught by the LoopManager and sent to DLQ
        """
        pass


class ProducerNode(BaseNode):
    """
    Abstract base class for producer nodes.
    
    Producer nodes mark the start of a loop iteration. They are called
    first each iteration and control the loop's timing and triggers.
    Producer nodes produce or fetch work units that drive the loop.
    """
    
    pass


class BlockingNode(BaseNode):
    """
    Abstract base class for blocking nodes.
    
    Blocking nodes perform work that must be completed before continuation.
    The LoopManager awaits the blocking node and all downstream blocking
    children to complete before proceeding. They form strict sequential
    async paths within the workflow.
    """
    
    pass


class NonBlockingNode(BaseNode):
    """
    Abstract base class for non-blocking nodes.
    
    Non-blocking nodes semantically mark the loop-end in the execution model.
    They perform computation or transformation but do not force the Producer
    to wait for downstream operations. After execution, the iteration ends
    and control returns to the Producer.
    """
    
    pass


class QueueNode(NonBlockingNode):
    """
    Concrete implementation of a non-blocking node that writes to a queue.
    
    QueueNode writes/publishes data to a Redis-backed queue via QueueManager.
    It acts as the loop end marker in the execution model. After execution
    completes, the LoopManager immediately returns to the Producer.
    """
    
    def __init__(self, node_config: NodeConfig, queue_name: str, queue_manager=None):
        """
        Initialize QueueNode.
        
        Args:
            node_config: Static configuration for this node
            queue_name: Name of the queue to write to
            queue_manager: QueueManager instance (injected dependency)
        """
        super().__init__(node_config)
        self._queue_name = queue_name
        self._queue_manager = queue_manager
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the queue node by pushing data to the queue.
        
        Args:
            node_data: Data to push to the queue
            
        Returns:
            NodeData: Returns the same data (no transformation)
        """
        if self._queue_manager is None:
            raise RuntimeError("QueueManager not provided to QueueNode")
        
        await self._queue_manager.push(self._queue_name, node_data)
        return node_data


class QueueReader(ProducerNode):
    """
    Concrete implementation of a producer node that reads from a queue.
    
    QueueReader begins a new loop iteration by reading from a Redis queue
    using QueueManager.pop(). It awaits data from the queue and starts
    a new loop iteration. The orchestrator treats it as the loop entry point.
    """
    
    def __init__(
        self,
        node_config: NodeConfig,
        queue_name: str,
        queue_manager=None,
        timeout: float = 5.0
    ):
        """
        Initialize QueueReader.
        
        Args:
            node_config: Static configuration for this node
            queue_name: Name of the queue to read from
            queue_manager: QueueManager instance (injected dependency)
            timeout: Timeout in seconds for blocking pop operation
        """
        super().__init__(node_config)
        self._queue_name = queue_name
        self._queue_manager = queue_manager
        self._timeout = timeout
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the queue reader by popping data from the queue.
        
        This method blocks (with timeout) until data is available in the queue.
        If no data is available within the timeout, it returns empty NodeData.
        
        Args:
            node_data: Input data (typically empty for queue readers)
            
        Returns:
            NodeData: Data popped from the queue, or empty NodeData if timeout
        """
        if self._queue_manager is None:
            raise RuntimeError("QueueManager not provided to QueueReader")
        
        result = await self._queue_manager.pop(self._queue_name, self._timeout)
        
        if result is None:
            # Timeout - return empty data to allow loop to continue
            return NodeData()
        
        return result
