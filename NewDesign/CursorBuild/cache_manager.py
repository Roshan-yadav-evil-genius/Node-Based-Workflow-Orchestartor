"""
Redis cache manager for Development Mode node state.

This module manages the Redis cache used in Development Mode to store
node execution outputs, enabling step-through debugging and iterative
node execution following the Single Responsibility Principle.
"""

from typing import Optional

from domain import NodeData
from serialization import Serializer


class CacheManager:
    """
    Manages Redis cache for Development Mode node state.
    
    Stores and retrieves node execution outputs to enable dependency
    resolution and step-through execution in Development Mode.
    """
    
    def __init__(self, redis_client, key_prefix: str = "node_output:"):
        """
        Initialize CacheManager with Redis client.
        
        Args:
            redis_client: Redis client instance (must support async operations)
            key_prefix: Prefix for cache keys (default: "node_output:")
        """
        self._redis = redis_client
        self._serializer = Serializer()
        self._key_prefix = key_prefix
    
    def _get_key(self, node_id: str) -> str:
        """Generate cache key for a node ID."""
        return f"{self._key_prefix}{node_id}"
    
    async def get_node_output(self, node_id: str) -> Optional[NodeData]:
        """
        Retrieve cached output for a node.
        
        Args:
            node_id: Unique identifier of the node
            
        Returns:
            Optional[NodeData]: Cached output data, or None if not found
        """
        key = self._get_key(node_id)
        serialized = await self._redis.get(key)
        
        if serialized is None:
            return None
        
        return self._serializer.deserialize(serialized)
    
    async def set_node_output(self, node_id: str, data: NodeData, ttl: Optional[int] = None) -> None:
        """
        Store node output in cache.
        
        Args:
            node_id: Unique identifier of the node
            data: NodeData to store
            ttl: Optional time-to-live in seconds
        """
        key = self._get_key(node_id)
        serialized = self._serializer.serialize(data)
        
        if ttl is not None:
            await self._redis.setex(key, ttl, serialized)
        else:
            await self._redis.set(key, serialized)
    
    async def clear_node_output(self, node_id: str) -> None:
        """
        Clear cached output for a specific node.
        
        Args:
            node_id: Unique identifier of the node
        """
        key = self._get_key(node_id)
        await self._redis.delete(key)
    
    async def clear_all(self) -> None:
        """
        Clear all cached node outputs.
        
        This uses a pattern match to find all keys with the prefix
        and deletes them.
        """
        pattern = f"{self._key_prefix}*"
        keys = []
        
        # Scan for all keys matching the pattern
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await self._redis.delete(*keys)
    
    async def has_output(self, node_id: str) -> bool:
        """
        Check if a node has cached output.
        
        Args:
            node_id: Unique identifier of the node
            
        Returns:
            bool: True if output exists, False otherwise
        """
        key = self._get_key(node_id)
        return await self._redis.exists(key) > 0
    
    async def get_all_node_ids(self) -> list[str]:
        """
        Get list of all node IDs that have cached outputs.
        
        Returns:
            list[str]: List of node IDs with cached outputs
        """
        pattern = f"{self._key_prefix}*"
        node_ids = []
        
        async for key in self._redis.scan_iter(match=pattern):
            # Remove prefix to get node_id
            node_id = key.decode('utf-8').replace(self._key_prefix, '')
            node_ids.append(node_id)
        
        return node_ids
