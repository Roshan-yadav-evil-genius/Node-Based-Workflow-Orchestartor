"""
Workflow Graph implementation for managing node connections and DAG structure.
Single Responsibility: Manage node connections and graph structure.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict, deque
from .base_node import Node
from .blocking_node import BlockingNode
from .non_blocking_node import NonBlockingNode


class WorkflowGraph:
    """
    Represents a Directed Acyclic Graph (DAG) of workflow nodes.
    Manages connections between nodes and provides graph traversal utilities.
    """

    def __init__(self):
        """Initialize an empty workflow graph."""
        self._nodes: Set[Node] = set()
        self._edges: Dict[Node, List[Tuple[Node, Optional[str]]]] = defaultdict(list)
        self._reverse_edges: Dict[Node, List[Node]] = defaultdict(list)
        self._blocking_cache: Dict[Node, bool] = {}

    def add_node(self, node: Node) -> None:
        """
        Add a node to the graph.
        
        Args:
            node: The node to add
        """
        self._nodes.add(node)
        # Clear cache when graph structure changes
        self._blocking_cache.clear()

    def connect(
        self,
        source: Node,
        target: Node,
        branch: Optional[str] = None
    ) -> None:
        """
        Connect a source node to a target node.
        
        Args:
            source: Source node
            target: Target node
            branch: Optional branch identifier (for IF nodes: "yes" or "no")
            
        Raises:
            ValueError: If nodes are not in the graph or connection creates a cycle
        """
        if source not in self._nodes:
            raise ValueError(f"Source node {source.identifier} not in graph")
        if target not in self._nodes:
            raise ValueError(f"Target node {target.identifier} not in graph")

        # Check for cycles (simple check - if target can reach source)
        if self._would_create_cycle(source, target):
            raise ValueError(
                f"Connection from {source.identifier} to {target.identifier} would create a cycle"
            )

        self._edges[source].append((target, branch))
        self._reverse_edges[target].append(source)
        # Clear cache when graph structure changes
        self._blocking_cache.clear()

    def _would_create_cycle(self, source: Node, target: Node) -> bool:
        """
        Check if adding an edge from source to target would create a cycle.
        
        Args:
            source: Source node
            target: Target node
            
        Returns:
            True if cycle would be created, False otherwise
        """
        # Use BFS to check if target can reach source
        visited: Set[Node] = set()
        queue = deque([target])

        while queue:
            current = queue.popleft()
            if current == source:
                return True
            if current in visited:
                continue
            visited.add(current)

            for next_node, _ in self._edges.get(current, []):
                if next_node not in visited:
                    queue.append(next_node)

        return False

    def get_downstream(
        self,
        node: Node,
        branch: Optional[str] = None
    ) -> List[Node]:
        """
        Get downstream nodes from a given node.
        
        Args:
            node: Source node
            branch: Optional branch filter (for IF nodes)
            
        Returns:
            List of downstream nodes
        """
        if node not in self._nodes:
            return []

        downstream = []
        for target, target_branch in self._edges.get(node, []):
            if branch is None or target_branch == branch:
                downstream.append(target)

        return downstream

    def get_upstream(self, node: Node) -> List[Node]:
        """
        Get upstream nodes for a given node.
        
        Args:
            node: Target node
            
        Returns:
            List of upstream nodes
        """
        if node not in self._nodes:
            return []
        return list(self._reverse_edges.get(node, []))

    def contains_blocking_downstream(
        self,
        node: Node,
        visited: Optional[Set[Node]] = None
    ) -> bool:
        """
        Check if any downstream path from this node contains a BlockingNode.
        Uses caching for performance.
        
        Args:
            node: Starting node
            visited: Set of visited nodes (for cycle detection)
            
        Returns:
            True if downstream path contains a BlockingNode, False otherwise
        """
        if node in self._blocking_cache:
            return self._blocking_cache[node]

        if visited is None:
            visited = set()

        if node in visited:
            # Cycle detected, assume blocking to be safe
            return True

        visited.add(node)

        # Check if current node is blocking
        if isinstance(node, BlockingNode):
            self._blocking_cache[node] = True
            visited.remove(node)
            return True

        # Check all downstream paths
        downstream = self.get_downstream(node)
        if not downstream:
            # No downstream nodes - not blocking
            self._blocking_cache[node] = False
            visited.remove(node)
            return False

        # Check if any downstream path contains blocking
        for next_node in downstream:
            if self.contains_blocking_downstream(next_node, visited.copy()):
                self._blocking_cache[node] = True
                visited.remove(node)
                return True

        # No blocking nodes found in any downstream path
        self._blocking_cache[node] = False
        visited.remove(node)
        return False

    def get_all_nodes(self) -> Set[Node]:
        """
        Get all nodes in the graph.
        
        Returns:
            Set of all nodes
        """
        return self._nodes.copy()

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate that the graph is a valid DAG.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for cycles using topological sort
        in_degree: Dict[Node, int] = {node: 0 for node in self._nodes}
        for source in self._edges:
            for target, _ in self._edges[source]:
                in_degree[target] += 1

        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        processed = 0

        while queue:
            node = queue.popleft()
            processed += 1

            for target, _ in self._edges.get(node, []):
                in_degree[target] -= 1
                if in_degree[target] == 0:
                    queue.append(target)

        if processed != len(self._nodes):
            return False, "Graph contains cycles"

        return True, None

