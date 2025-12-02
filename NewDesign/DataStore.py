import asyncio
import structlog
from typing import Any, Dict, Optional

logger = structlog.get_logger(__name__)

class DataStore:
    """
    Redis-backed data store for cross-loop communication and state management.
    Handles queues, caching, and other shared data operations.
    
    Currently uses in-memory asyncio.Queue as a placeholder for Redis implementation.
    """
    _shared_instance = None
    
    def __init__(self):
        # In a real implementation, this would be a Redis client.
        # For now, we use an in-memory dictionary of asyncio.Queues.
        self._queues: Dict[str, asyncio.Queue] = {}
    
    @classmethod
    def set_shared_instance(cls, instance):
        """
        Set the shared DataStore instance.
        
        This should be called by the WorkflowOrchestrator during initialization
        to make the DataStore available globally to all nodes.
        
        Args:
            instance: DataStore instance to set as shared
        """
        cls._shared_instance = instance
        return cls._shared_instance
    
    @classmethod
    def get_shared_instance(cls):
        """
        Get the shared DataStore instance.
        
        Returns:
            DataStore: The shared DataStore instance
            
        Raises:
            RuntimeError: If shared instance has not been initialized
        """
        if cls._shared_instance is None:
            raise RuntimeError(
                "DataStore shared instance not initialized. "
                "Ensure WorkflowOrchestrator is initialized first."
            )
        return cls._shared_instance
    
    @classmethod
    def reset_shared_instance(cls):
        """
        Reset shared instance (for testing).
        
        This method is useful in test scenarios where you need to reset
        the shared instance between tests.
        """
        cls._shared_instance = None

    async def get_queue(self, queue_name: str) -> asyncio.Queue:
        """
        Get or create a queue by name.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            asyncio.Queue: The queue instance
        """
        if queue_name not in self._queues:
            self._queues[queue_name] = asyncio.Queue()
        return self._queues[queue_name]

    async def push(self, queue_name: str, data: Any):
        """
        Push data to a named queue.
        
        In a real implementation, this would push to Redis.
        Currently uses in-memory asyncio.Queue as placeholder.
        
        Args:
            queue_name: Name of the queue
            data: Data to push to the queue
        """
        queue = await self.get_queue(queue_name)
        await queue.put(data)
        logger.info(f"[DataStore] Pushed to '{queue_name}': {data}")

    async def pop(self, queue_name: str, timeout: Optional[float] = None) -> Any:
        """
        Pop data from a named queue.
        
        In a real implementation, this would pop from Redis.
        Currently uses in-memory asyncio.Queue as placeholder.
        
        Args:
            queue_name: Name of the queue
            timeout: Optional timeout in seconds for blocking pop operation
            
        Returns:
            Any: Data popped from the queue, or None if timeout occurs
        """
        queue = await self.get_queue(queue_name)
        if timeout:
            try:
                return await asyncio.wait_for(queue.get(), timeout)
            except asyncio.TimeoutError:
                return None
        return await queue.get()
