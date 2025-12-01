"""
Serialization utilities for NodeData.

This module handles serialization and deserialization of NodeData instances
for storage in Redis (queues, cache, DLQ).
"""

import json
from typing import Any, Dict

from domain import NodeData


class Serializer:
    """
    Handles serialization/deserialization of NodeData for Redis storage.
    
    Uses JSON format for serialization. All methods are synchronous as they
    operate on in-memory data structures.
    """
    
    @staticmethod
    def serialize(data: NodeData) -> bytes:
        """
        Convert NodeData to bytes for Redis storage.
        
        Args:
            data: NodeData instance to serialize
            
        Returns:
            bytes: Serialized data as JSON bytes
            
        Raises:
            TypeError: If data cannot be serialized to JSON
        """
        try:
            serializable_data = {
                "data": data.data,
                "metadata": data.metadata,
            }
            json_str = json.dumps(serializable_data, default=_json_default)
            return json_str.encode('utf-8')
        except (TypeError, ValueError) as e:
            raise TypeError(f"Failed to serialize NodeData: {e}") from e
    
    @staticmethod
    def deserialize(data: bytes) -> NodeData:
        """
        Convert bytes back to NodeData instance.
        
        Args:
            data: Serialized bytes from Redis
            
        Returns:
            NodeData: Deserialized NodeData instance
            
        Raises:
            ValueError: If data cannot be deserialized
        """
        try:
            json_str = data.decode('utf-8')
            parsed = json.loads(json_str)
            
            if not isinstance(parsed, dict):
                raise ValueError("Deserialized data must be a dictionary")
            
            return NodeData(
                data=parsed.get("data", {}),
                metadata=parsed.get("metadata", {})
            )
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to deserialize NodeData: {e}") from e
    
    @staticmethod
    def serialize_dict(data: Dict[str, Any]) -> bytes:
        """
        Serialize a dictionary directly to bytes.
        
        Useful for serializing arbitrary data structures.
        
        Args:
            data: Dictionary to serialize
            
        Returns:
            bytes: Serialized data as JSON bytes
        """
        try:
            json_str = json.dumps(data, default=_json_default)
            return json_str.encode('utf-8')
        except (TypeError, ValueError) as e:
            raise TypeError(f"Failed to serialize dictionary: {e}") from e
    
    @staticmethod
    def deserialize_dict(data: bytes) -> Dict[str, Any]:
        """
        Deserialize bytes to a dictionary.
        
        Args:
            data: Serialized bytes
            
        Returns:
            Dict: Deserialized dictionary
        """
        try:
            json_str = data.decode('utf-8')
            return json.loads(json_str)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to deserialize dictionary: {e}") from e


def _json_default(obj: Any) -> Any:
    """
    Default JSON encoder for non-serializable types.
    
    Handles common non-serializable types by converting them to strings
    or serializable representations.
    """
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    elif hasattr(obj, '__str__'):
        return str(obj)
    else:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
