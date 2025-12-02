from typing import Optional, Dict, Type
import pkgutil
import importlib
import inspect
from Nodes.BaseNode import BaseNode
from Nodes.NodeConfig import NodeConfig
from Nodes.ProducerNode import ProducerNode
from Nodes.BlockingNode import BlockingNode
from Nodes.NonBlockingNode import NonBlockingNode


class NodeFactory:
    """
    Factory class responsible for creating node instances from node type and config.
    Follows Single Responsibility Principle - only handles node creation.
    Auto-discovers node classes by scanning the Nodes package.
    """
    
    # Registry cache - initialized to None, populated on first access
    _node_registry: Optional[Dict[str, Type[BaseNode]]] = None
    
    # Abstract base classes to exclude from discovery
    _abstract_base_classes = {BaseNode, ProducerNode, BlockingNode, NonBlockingNode}
    
    @classmethod
    def _discover_node_classes(cls) -> Dict[str, Type[BaseNode]]:
        """
        Auto-discover all node classes in the Nodes package.
        
        Scans the Nodes package, imports all modules, and finds classes that inherit
        from ProducerNode, BlockingNode, or NonBlockingNode. Builds a mapping from
        each class's identifier to the class itself.
        
        Returns:
            Dictionary mapping node type identifiers to node classes
            
        Raises:
            ValueError: If duplicate identifiers are found
        """
        import Nodes
        
        # Get the path to the Nodes package
        nodes_package_path = Nodes.__path__
        nodes_package_name = Nodes.__name__
        
        discovered_classes = []
        
        # Iterate through all modules in the Nodes package
        for importer, modname, ispkg in pkgutil.iter_modules(nodes_package_path, nodes_package_name + "."):
            if ispkg:
                continue
            
            try:
                # Import the module
                module = importlib.import_module(modname)
                
                # Find all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if class is defined in this module (not imported)
                    if obj.__module__ != modname:
                        continue
                    
                    # Check if class inherits from one of our base node types
                    if (issubclass(obj, ProducerNode) or 
                        issubclass(obj, BlockingNode) or 
                        issubclass(obj, NonBlockingNode)):
                        # Exclude abstract base classes
                        if obj not in cls._abstract_base_classes:
                            discovered_classes.append(obj)
            except Exception as e:
                # Log but continue - some modules might fail to import
                print(f"[NodeFactory] Warning: Failed to import module {modname}: {e}")
                continue
        
        # Build mapping from identifier to class
        mapping = {}
        identifier_to_classes = {}  # For duplicate detection
        
        for node_class in discovered_classes:
            try:
                identifier = node_class.identifier()
                
                # Track which classes have this identifier (for duplicate detection)
                if identifier not in identifier_to_classes:
                    identifier_to_classes[identifier] = []
                identifier_to_classes[identifier].append(node_class)
                
                mapping[identifier] = node_class
            except Exception as e:
                print(f"[NodeFactory] Warning: Failed to get identifier from {node_class.__name__}: {e}")
                continue
        
        # Validate uniqueness
        duplicates = {ident: classes for ident, classes in identifier_to_classes.items() 
                     if len(classes) > 1}
        if duplicates:
            error_msg = "Duplicate node identifiers found:\n"
            for ident, classes in duplicates.items():
                class_names = [cls.__name__ for cls in classes]
                error_msg += f"  '{ident}': {', '.join(class_names)}\n"
            raise ValueError(error_msg)
        
        print(f"[NodeFactory] Auto-discovered {len(mapping)} node classes")
        return mapping
    
    @classmethod
    def _ensure_registry_loaded(cls) -> None:
        """
        Ensure the node registry is loaded. Loads it if it hasn't been loaded yet.
        """
        if cls._node_registry is None:
            cls._node_registry = cls._discover_node_classes()
    
    @classmethod
    def create_node(cls, node_type: str, config: NodeConfig) -> Optional[BaseNode]:
        """
        Create a node instance based on node type and configuration.
        
        Args:
            node_type: String identifier for the node type
            config: NodeConfig object with node configuration
            
        Returns:
            BaseNode instance or None if node type is unknown
        """
        # Ensure registry is loaded (lazy initialization)
        cls._ensure_registry_loaded()
        
        # Get node class from registry
        node_cls = cls._node_registry.get(node_type)
        if node_cls:
            return node_cls(config)
        
        print(f"[NodeFactory] Warning: Unknown node type '{node_type}'")
        return None
