from typing import Dict, List, Set, Tuple
from Nodes.BaseNode import BaseNode
from Nodes.NonBlockingNode import NonBlockingNode
from rich import print

class GraphTraverser:
    """
    Class responsible for traversing workflow graph to find loops and chains.
    Follows Single Responsibility Principle - only handles graph traversal logic.
    """
    
    def __init__(self, nodes: Dict[str, BaseNode]):
        """
        Initialize GraphTraverser.
        
        Args:
            nodes: Dictionary mapping node IDs to BaseNode instances
        """
        self.nodes = nodes
    
    def find_loops(self, edge_map: Dict[str, List[Dict[str, str]]], producer_nodes: List[str]) -> List[Tuple[str, List[str], Dict[str, List[str]]]]:
        """
        Find all loops starting from ProducerNodes.
        
        Args:
            edge_map: Dictionary mapping source node IDs to list of edge dictionaries
            producer_nodes: List of ProducerNode IDs
            
        Returns:
            List of tuples: (producer_id, chain_ids, branch_info) for each loop
        """
        loops = []
        for producer_id in producer_nodes:
            chain_ids, branch_info = self._traverse_chain_from_producer(producer_id, edge_map)
            loops.append((producer_id, chain_ids, branch_info))
        return loops
    
    def _traverse_chain_from_producer(self, producer_id: str, edge_map: Dict[str, List[Dict[str, str]]]) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Traverse the graph from a ProducerNode following edges until a NonBlockingNode is reached.
        Handles conditional branches by following all paths.
        
        Args:
            producer_id: ID of the ProducerNode to start traversal from
            edge_map: Dictionary mapping source node IDs to list of edge dictionaries
            
        Returns:
            Tuple of (chain of node IDs, branch information dictionary)
        """
        chain_ids: List[str] = []
        branch_info: Dict[str, List[str]] = {}  # {branch_label: [node_ids]}
        visited: Set[str] = {producer_id}  # Track visited nodes to avoid cycles
        current_id = producer_id
        
        while current_id in edge_map:
            # Get next edges from edge map
            next_edges = edge_map[current_id]
            
            if not next_edges:
                break
            
            # Check if this is a branching node (multiple outgoing edges)
            if len(next_edges) > 1:
                # Branching node - add it to chain first if not already added
                if current_id not in chain_ids and current_id != producer_id:
                    chain_ids.append(current_id)
                    visited.add(current_id)
                
                # Follow all branches and collect nodes maintaining order
                all_branch_nodes: List[str] = []
                branch_visited_combined: Set[str] = visited.copy()
                
                for edge in next_edges:
                    branch_target = edge["target"]
                    branch_label = edge.get("label") or "default"  # Use "default" if no label
                    
                    # Traverse this branch with a fresh visited set for this branch
                    branch_chain = self._traverse_branch(
                        branch_target, 
                        edge_map, 
                        branch_visited_combined.copy(),  # Use a copy to allow parallel branches
                        branch_label
                    )
                    
                    # Store branch information
                    if branch_label not in branch_info:
                        branch_info[branch_label] = []
                    branch_info[branch_label].extend(branch_chain)
                    
                    # Add nodes from this branch to the combined list
                    for node_id in branch_chain:
                        if node_id not in all_branch_nodes:
                            all_branch_nodes.append(node_id)
                        branch_visited_combined.add(node_id)
                
                # Add all nodes from all branches to the chain
                for node_id in all_branch_nodes:
                    if node_id not in chain_ids:
                        chain_ids.append(node_id)
                        visited.add(node_id)
                
                # After processing branches, we've reached NonBlockingNodes, so stop
                break
            else:
                # Single edge - follow normally
                next_edge = next_edges[0]
                next_id = next_edge["target"]
                
                # Check if we've already visited this node (cycle detection)
                if next_id in visited:
                    print(f"[GraphTraverser] Warning: Cycle detected at node {next_id}, stopping traversal")
                    break
                
                # Check if node exists
                if next_id not in self.nodes:
                    print(f"[GraphTraverser] Warning: Node {next_id} referenced in edges but not found")
                    break
                
                # Add to chain
                chain_ids.append(next_id)
                visited.add(next_id)
                
                # Check if this is a NonBlockingNode (marks loop end)
                next_node = self.nodes[next_id]
                if isinstance(next_node, NonBlockingNode):
                    # Found loop end marker
                    break
                
                # Continue to next node
                current_id = next_id
        
        return chain_ids, branch_info
    
    def _traverse_branch(self, start_id: str, edge_map: Dict[str, List[Dict[str, str]]], visited: Set[str], branch_label: str = None) -> List[str]:
        """
        Traverse a single branch from a starting node until a NonBlockingNode is reached.
        
        Args:
            start_id: ID of the node to start branch traversal from
            edge_map: Dictionary mapping source node IDs to list of edge dictionaries
            visited: Set of already visited node IDs (to avoid cycles)
            branch_label: Optional label for this branch (Yes/No)
            
        Returns:
            List of node IDs in this branch
        """
        branch_chain: List[str] = []
        current_id = start_id
        
        while current_id:
            # Check if node exists
            if current_id not in self.nodes:
                print(f"[GraphTraverser] Warning: Node {current_id} referenced in edges but not found")
                break
            
            # Check for cycles
            if current_id in visited:
                print(f"[GraphTraverser] Warning: Cycle detected at node {current_id} in branch")
                break
            
            # Add to branch chain
            branch_chain.append(current_id)
            visited.add(current_id)
            
            # Check if this is a NonBlockingNode (marks branch end)
            current_node = self.nodes[current_id]
            if isinstance(current_node, NonBlockingNode):
                # Found branch end marker
                break
            
            # Get next edges
            if current_id not in edge_map:
                # No more edges, end of branch
                break
            
            next_edges = edge_map[current_id]
            if not next_edges:
                break
            
            # If multiple edges, follow all branches recursively
            if len(next_edges) > 1:
                # Another branching point - collect all branches
                sub_branch_visited = visited.copy()
                for edge in next_edges:
                    branch_target = edge["target"]
                    sub_branch_chain = self._traverse_branch(
                        branch_target,
                        edge_map,
                        sub_branch_visited.copy(),
                        edge.get("label")
                    )
                    # Add nodes maintaining order
                    for node_id in sub_branch_chain:
                        if node_id not in branch_chain:
                            branch_chain.append(node_id)
                        sub_branch_visited.add(node_id)
                break
            else:
                # Single edge - continue
                current_id = next_edges[0]["target"]
        
        return branch_chain
