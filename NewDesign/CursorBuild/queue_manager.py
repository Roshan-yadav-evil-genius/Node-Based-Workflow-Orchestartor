"""
Redis-backed queue manager for cross-loop communication.

This module provides an abstraction over Redis queue operations, handling
serialization and multi-process safe queue operations following the
Single Responsibility Principle.
"""

from typing import Optional

from domain import NodeData
from serialization import Serializer


class QueueManager:
    """
    Manages Redis-backed queues for cross-loop communication.
    
    All methods are async and handle serialization/deserialization of
    NodeData automatically. Queues are multi-process safe via Redis.
    """
    
    def __init__(self, redis_client):
        """
        Initialize QueueManager with Redis client.
        
        Args:
            redis_client: Redis client instance (must support async operations)
                         Expected to be redis.asyncio.Redis or compatible
        """
        self._redis = redis_client
        self._serializer = Serializer()
    
    async def push(self, queue_name: str, data: NodeData) -> None:
        """
        Push data to a queue (LPUSH operation).
        
        Args:
            queue_name: Name of the queue
            data: NodeData to push to the queue
            
        Raises:
            Exception: If Redis operation fails
        """
        serialized = self._serializer.serialize(data)
        await self._redis.lpush(queue_name, serialized)
    
    async def pop(self, queue_name: str, timeout: float = 5.0) -> Optional[NodeData]:
        """
        Pop data from a queue with blocking (BRPOP operation).
        
        Args:
            queue_name: Name of the queue
            timeout: Timeout in seconds (0 = no timeout, blocks indefinitely)
            
        Returns:
            Optional[NodeData]: Popped data, or None if timeout occurs
            
        Raises:
            Exception: If Redis operation fails
        """
        try:
            # BRPOP returns a tuple (queue_name, value) or None on timeout
            result = await self._redis.brpop(queue_name, timeout=int(timeout))
            
            if result is None:
                return None
            
            # result is (queue_name, value) tuple
            _, serialized_data = result
            return self._serializer.deserialize(serialized_data)
        
        except Exception as e:
            # Handle timeout and other errors
            if "timeout" in str(e).lower():
                return None
            raise
    
    async def get_queue_length(self, queue_name: str) -> int:
        """
        Get the current length of a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            int: Number of items in the queue
        """
        return await self._redis.llen(queue_name)
    
    async def clear_queue(self, queue_name: str) -> None:
        """
        Clear all items from a queue.
        
        Args:
            queue_name: Name of the queue to clear
        """
        await self._redis.delete(queue_name)
    
    async def peek(self, queue_name: str) -> Optional[NodeData]:
        """
        Peek at the last item in queue without removing it (RPEEK).
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Optional[NodeData]: Last item in queue, or None if empty
        """
        # Use LINDEX to get last item (index -1) without removing
        serialized = await self._redis.lindex(queue_name, -1)
        if serialized is None:
            return None
        return self._serializer.deserialize(serialized)
