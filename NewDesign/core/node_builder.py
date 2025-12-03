from typing import Any, Dict, Optional, Tuple
from Nodes.Core.BaseNode import BaseNode
from Nodes.Core.NodeConfig import NodeConfig
from core.node_factory import NodeFactory
from core.workflow_node import WorkflowNode


class NodeBuilder:
    """
    Class responsible for building WorkflowNode and BaseNode instances from node definitions.
    Follows Single Responsibility Principle - only handles node creation.
    """
    
    def __init__(self, node_factory: Optional[NodeFactory] = None):
        """
        Initialize NodeBuilder.
        
        Args:
            node_factory: NodeFactory instance (creates default if not provided)
        """
        self.node_factory = node_factory or NodeFactory()
    
    def build_node(self, node_def: Dict[str, Any]) -> Optional[Tuple[WorkflowNode, BaseNode]]:
        """
        Build WorkflowNode and BaseNode from node definition.
        
        Args:
            node_def: Dictionary containing node definition with keys: id, type, data
            
        Returns:
            Tuple of (WorkflowNode, BaseNode) if successful, None otherwise
        """
        node_id = node_def["id"]
        node_type = node_def["type"]
        node_data = node_def.get("data", {})
        
        # Extract config data
        config_data = node_data.get("config", {})
        config_data["node_id"] = node_id
        config_data["node_name"] = node_id  # Use ID as name for now
        
        # Create NodeConfig
        config = NodeConfig(**config_data)
        
        # Create BaseNode instance using factory
        base_node = self.node_factory.create_node(node_type, config)
        
        if not base_node:
            return None
        
        # Create WorkflowNode instance
        workflow_node = WorkflowNode(id=node_id)
        
        return (workflow_node, base_node)
