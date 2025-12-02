from dataclasses import dataclass
from typing import Dict, List
from Nodes.BaseNode import BaseNode


@dataclass
class WorkflowGraph:
    """
    Data class to hold workflow graph structure.
    Follows Single Responsibility Principle - only holds graph data.
    """
    nodes: Dict[str, BaseNode]  # Map of node ID to BaseNode instance
    edge_map: Dict[str, List[Dict[str, str]]]  # source -> [{"target": ..., "label": ...}]
    producer_nodes: List[str]  # List of node IDs that are ProducerNodes
