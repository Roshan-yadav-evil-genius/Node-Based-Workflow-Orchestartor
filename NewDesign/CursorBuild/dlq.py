"""
Dead Letter Queue manager for failed node executions.

This module handles routing failed node executions to a Dead Letter Queue
for offline inspection and reprocessing, following the Single Responsibility
Principle and the fail-fast error handling policy.
"""

import traceback
from datetime import datetime
from typing import Dict, List, Optional

from domain import NodeData
from serialization import Serializer


class DLQManager:
    """
    Manages Dead Letter Queue for failed node executions.
    
    Implements the immediate failure policy: all failed executions are
    immediately sent to DLQ with full context (node_id, data, error, timestamp).
    """
    
    def __init__(self, redis_client, dlq_name: str = "dlq"):
        """
        Initialize DLQManager with Redis client.
        
        Args:
            redis_client: Redis client instance (must support async operations)
            dlq_name: Name of the DLQ list in Redis (default: "dlq")
        """
        self._redis = redis_client
        self._serializer = Serializer()
        self._dlq_name = dlq_name
    
    async def send_to_dlq(
        self,
        node_id: str,
        node_data: NodeData,
        error: Exception
    ) -> None:
        """
        Send failed execution to Dead Letter Queue.
        
        Stores a structured record containing:
        - node_id: Identifier of the failed node
        - node_data: The payload that failed
        - error_message: Error message
        - error_type: Type of exception
        - traceback: Full traceback
        - timestamp: When the failure occurred
        
        Args:
            node_id: Unique identifier of the failed node
            node_data: The NodeData payload that failed
            error: The exception that was raised
        """
        error_record = {
            "node_id": node_id,
            "node_data": {
                "data": node_data.data,
                "metadata": node_data.metadata,
            },
            "error_message": str(error),
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        serialized = self._serializer.serialize_dict(error_record)
        await self._redis.lpush(self._dlq_name, serialized)
    
    async def get_dlq_items(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve DLQ items for inspection.
        
        Args:
            limit: Maximum number of items to retrieve
            
        Returns:
            List[Dict]: List of error records, most recent first
        """
        # Get items from DLQ (without removing them)
        items = await self._redis.lrange(self._dlq_name, 0, limit - 1)
        
        result = []
        for item in items:
            try:
                deserialized = self._serializer.deserialize_dict(item)
                result.append(deserialized)
            except Exception as e:
                # If we can't deserialize an item, include a placeholder
                result.append({
                    "error": f"Failed to deserialize DLQ item: {e}",
                    "raw_data": item.decode('utf-8', errors='ignore')[:100] if isinstance(item, bytes) else str(item)[:100]
                })
        
        return result
    
    async def get_dlq_length(self) -> int:
        """
        Get the current length of the DLQ.
        
        Returns:
            int: Number of items in the DLQ
        """
        return await self._redis.llen(self._dlq_name)
    
    async def clear_dlq(self) -> None:
        """
        Clear all items from the DLQ.
        
        Use with caution - this permanently removes all failed execution records.
        """
        await self._redis.delete(self._dlq_name)
    
    async def remove_dlq_item(self, index: int) -> Optional[Dict]:
        """
        Remove and return a specific DLQ item by index.
        
        Args:
            index: Index of the item to remove (0 = most recent)
            
        Returns:
            Optional[Dict]: The removed error record, or None if index is invalid
        """
        # Get the item
        item = await self._redis.lindex(self._dlq_name, index)
        if item is None:
            return None
        
        # Deserialize
        try:
            deserialized = self._serializer.deserialize_dict(item)
        except Exception as e:
            return {"error": f"Failed to deserialize DLQ item: {e}"}
        
        # Remove it using LSET + LTRIM (set to special value then trim)
        # Or use a more direct approach: get all, filter, and replace
        # For simplicity, we'll use a two-step process
        await self._redis.lset(self._dlq_name, index, "__DELETED__")
        await self._redis.lrem(self._dlq_name, 1, "__DELETED__")
        
        return deserialized
