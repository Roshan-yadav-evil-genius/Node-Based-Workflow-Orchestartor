"""
Node Registry for factory and registry pattern.
Single Responsibility: Factory and registry for node types.
"""

from typing import Dict, Callable, Any, Optional, List
from .base_node import Node


class NodeRegistry:
    """
    Registry and factory for creating node instances.
    Allows dynamic registration and creation of node types.
    """

    def __init__(self):
        """Initialize an empty node registry."""
        self._factories: Dict[str, Callable[[Dict[str, Any]], Node]] = {}
        self._node_types: Dict[str, type] = {}

    def register(
        self,
        node_type: str,
        factory: Optional[Callable[[Dict[str, Any]], Node]] = None,
        node_class: Optional[type] = None
    ) -> None:
        """
        Register a node type with the registry.
        
        Args:
            node_type: String identifier for the node type
            factory: Optional factory function that takes config and returns Node
            node_class: Optional node class (will create simple factory if provided)
            
        Raises:
            ValueError: If neither factory nor node_class is provided
        """
        if factory is None and node_class is None:
            raise ValueError("Either factory or node_class must be provided")

        if factory is not None:
            self._factories[node_type] = factory
        elif node_class is not None:
            # Create a simple factory that instantiates the class
            def simple_factory(config: Dict[str, Any]) -> Node:
                return node_class(**config)
            self._factories[node_type] = simple_factory
            self._node_types[node_type] = node_class

    def create(self, node_type: str, config: Optional[Dict[str, Any]] = None) -> Node:
        """
        Create a node instance of the specified type.
        
        Args:
            node_type: String identifier for the node type
            config: Optional configuration dictionary for the node
            
        Returns:
            Node instance
            
        Raises:
            ValueError: If node_type is not registered
        """
        if node_type not in self._factories:
            raise ValueError(f"Node type '{node_type}' is not registered")

        if config is None:
            config = {}

        return self._factories[node_type](config)

    def get_node_types(self) -> List[str]:
        """
        Get list of all registered node types.
        
        Returns:
            List of registered node type identifiers
        """
        return list(self._factories.keys())

    def is_registered(self, node_type: str) -> bool:
        """
        Check if a node type is registered.
        
        Args:
            node_type: String identifier for the node type
            
        Returns:
            True if registered, False otherwise
        """
        return node_type in self._factories

    def unregister(self, node_type: str) -> None:
        """
        Unregister a node type from the registry.
        
        Args:
            node_type: String identifier for the node type to unregister
        """
        self._factories.pop(node_type, None)
        self._node_types.pop(node_type, None)

