"""
Node factory for creating node instances from workflow definitions.

This module provides a factory pattern for instantiating appropriate node
classes based on workflow configuration, following the Single Responsibility Principle.
"""

from typing import Any, Dict, Optional, Type

from domain import NodeConfig, NodeType
from nodes import (
    BaseNode,
    BlockingNode,
    NonBlockingNode,
    ProducerNode,
    QueueNode,
    QueueReader,
)


class NodeFactory:
    """
    Factory for creating node instances from workflow definitions.
    
    Maps node types from JSON workflow definitions to Python node classes
    and handles node registration and instantiation.
    """
    
    # Registry of node type strings to node classes
    _node_registry: Dict[str, Type[BaseNode]] = {}
    
    @classmethod
    def register_node_type(cls, node_type: str, node_class: Type[BaseNode]) -> None:
        """
        Register a custom node type.
        
        Args:
            node_type: String identifier for the node type
            node_class: Python class that implements BaseNode
        """
        cls._node_registry[node_type] = node_class
    
    @classmethod
    def create_node(
        self,
        node_type: str,
        node_id: str,
        node_config_dict: Dict[str, Any],
        queue_manager=None
    ) -> BaseNode:
        """
        Create a node instance from workflow definition.
        
        Args:
            node_type: Type of node (e.g., 'producer', 'blocking', 'non-blocking', 'queue', 'queue-reader')
            node_id: Unique identifier for the node
            node_config_dict: Configuration dictionary from workflow JSON
            queue_manager: Optional QueueManager instance for queue nodes
            
        Returns:
            BaseNode: Instantiated node instance
            
        Raises:
            ValueError: If node_type is not recognized
        """
        # Extract execution pool from config
        execution_pool_str = node_config_dict.get('execution_pool', 'async')
        execution_pool = self._parse_execution_pool(execution_pool_str)
        
        # Create NodeConfig
        node_config = NodeConfig(
            node_id=node_id,
            node_type=node_type,
            execution_pool=execution_pool,
            config=node_config_dict.get('config', {})
        )
        
        # Check if custom node type is registered
        if node_type in self._node_registry:
            node_class = self._node_registry[node_type]
            return node_class(node_config)
        
        # Handle built-in node types
        node_type_lower = node_type.lower()
        
        if node_type_lower == 'queue':
            queue_name = node_config_dict.get('queue_name')
            if not queue_name:
                raise ValueError(f"QueueNode '{node_id}' requires 'queue_name' in config")
            return QueueNode(node_config, queue_name, queue_manager)
        
        elif node_type_lower == 'queue-reader' or node_type_lower == 'queuereader':
            queue_name = node_config_dict.get('queue_name')
            if not queue_name:
                raise ValueError(f"QueueReader '{node_id}' requires 'queue_name' in config")
            timeout = node_config_dict.get('timeout', 5.0)
            return QueueReader(node_config, queue_name, queue_manager, timeout)
        
        elif node_type_lower == 'producer':
            # Return abstract ProducerNode - users should subclass this
            # For now, we'll create a basic implementation
            return _BasicProducerNode(node_config)
        
        elif node_type_lower == 'blocking':
            # Return abstract BlockingNode - users should subclass this
            return _BasicBlockingNode(node_config)
        
        elif node_type_lower == 'non-blocking' or node_type_lower == 'nonblocking':
            # Return abstract NonBlockingNode - users should subclass this
            return _BasicNonBlockingNode(node_config)
        
        else:
            raise ValueError(f"Unknown node type: {node_type}")
    
    @staticmethod
    def _parse_execution_pool(pool_str: str) -> Any:
        """Parse execution pool string to ExecutionPool enum."""
        from domain import ExecutionPool
        
        pool_str_lower = pool_str.lower()
        if pool_str_lower == 'async':
            return ExecutionPool.ASYNC
        elif pool_str_lower == 'thread':
            return ExecutionPool.THREAD
        elif pool_str_lower == 'process':
            return ExecutionPool.PROCESS
        else:
            # Default to ASYNC if unknown
            return ExecutionPool.ASYNC


# Basic implementations for abstract node types
# These are placeholders - users should subclass and implement their own logic

class _BasicProducerNode(ProducerNode):
    """Basic producer node implementation for factory use."""
    
    async def execute(self, node_data):
        """Basic implementation - returns data unchanged."""
        return node_data


class _BasicBlockingNode(BlockingNode):
    """Basic blocking node implementation for factory use."""
    
    async def execute(self, node_data):
        """Basic implementation - returns data unchanged."""
        return node_data


class _BasicNonBlockingNode(NonBlockingNode):
    """Basic non-blocking node implementation for factory use."""
    
    async def execute(self, node_data):
        """Basic implementation - returns data unchanged."""
        return node_data
