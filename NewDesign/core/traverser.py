import structlog
from typing import Dict, List, Set, Tuple, Optional
from Nodes.Core.NonBlockingNode import NonBlockingNode
from core.graph import WorkflowGraph
from core.utils import BranchKeyNormalizer

logger = structlog.get_logger(__name__)

class GraphTraverser:
    """
    Class responsible for traversing workflow graph to find loops and chains.
    Follows Single Responsibility Principle - only handles graph traversal logic.
    """
    
    def __init__(self, workflow_graph: WorkflowGraph):
        """
        Initialize GraphTraverser.
        
        Args:
            workflow_graph: WorkflowGraph instance to traverse
        """
        self.workflow_graph = workflow_graph
    
    def find_loops(self) -> List[Tuple[str, List[str], Dict[str, List[str]]]]:
        """
        Find all loops starting from ProducerNodes.
        
        Returns:
            List of tuples: (producer_id, chain_ids, branch_info) for each loop
        """
        loops = []
        for producer_id in self.workflow_graph.producer_node_ids:
            chain_ids, branch_info = self._traverse_chain_from_producer(producer_id)
            loops.append((producer_id, chain_ids, branch_info))
        return loops
    
    def _traverse_chain_from_producer(self, producer_id: str) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Traverse the graph from a ProducerNode following edges until a NonBlockingNode is reached.
        Handles conditional branches by following all paths.
        
        Args:
            producer_id: ID of the ProducerNode to start traversal from
            
        Returns:
            Tuple of (chain of node IDs, branch information dictionary)
        """
        chain_ids: List[str] = []
        branch_info: Dict[str, List[str]] = {}  # {branch_label: [node_ids]}
        visited: Set[str] = {producer_id}  # Track visited nodes to avoid cycles
        current_id = producer_id
        
        while current_id:
            current_node = self.workflow_graph.get_node(current_id)
            if not current_node:
                break
            
            # Get all next nodes using the linked structure
            next_nodes = self.workflow_graph.get_all_next(current_id)
            
            if not next_nodes:
                break
            
            # Check if this is a branching node (multiple outgoing edges)
            if len(next_nodes) > 1:
                # Branching node - add it to chain first if not already added
                if current_id not in chain_ids and current_id != producer_id:
                    chain_ids.append(current_id)
                    visited.add(current_id)
                
                # Follow all branches and collect nodes maintaining order
                all_branch_nodes: List[str] = []
                branch_visited_combined: Set[str] = visited.copy()
                
                for branch_key, next_workflow_node in next_nodes.items():
                    branch_target = next_workflow_node.id
                    
                    # Convert lowercase keys back to capitalized format for backward compatibility
                    branch_label = BranchKeyNormalizer.normalize_to_capitalized(branch_key)
                    
                    # Traverse this branch with a fresh visited set for this branch
                    branch_chain = self._traverse_branch(
                        branch_target, 
                        branch_visited_combined.copy(),  # Use a copy to allow parallel branches
                        branch_label
                    )
                    
                    # Store branch information (use "default" if no label)
                    branch_label_key = branch_label or "default"
                    if branch_label_key not in branch_info:
                        branch_info[branch_label_key] = []
                    branch_info[branch_label_key].extend(branch_chain)
                    
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
                next_workflow_node = list(next_nodes.values())[0]
                next_id = next_workflow_node.id
                
                # Validate and process next node
                if not self._validate_and_add_node(next_id, visited, chain_ids):
                    break
                
                # Check if this is a NonBlockingNode (marks loop end)
                if self._is_non_blocking_node(next_id):
                    break
                
                # Continue to next node
                current_id = next_id
        
        return chain_ids, branch_info
    
    def _traverse_branch(self, start_id: str, visited: Set[str], branch_label: str = None) -> List[str]:
        """
        Traverse a single branch from a starting node until a NonBlockingNode is reached.
        
        Args:
            start_id: ID of the node to start branch traversal from
            visited: Set of already visited node IDs (to avoid cycles)
            branch_label: Optional label for this branch (Yes/No)
            
        Returns:
            List of node IDs in this branch
        """
        branch_chain: List[str] = []
        current_id = start_id
        
        while current_id:
            # Validate and process current node
            if not self._validate_and_add_node(current_id, visited, branch_chain):
                break
            
            # Check if this is a NonBlockingNode (marks branch end)
            if self._is_non_blocking_node(current_id):
                break
            
            # Get next nodes using the linked structure
            next_nodes = self.workflow_graph.get_all_next(current_id)
            if not next_nodes:
                # No more edges, end of branch
                break
            
            # If multiple edges, follow all branches recursively
            if len(next_nodes) > 1:
                # Another branching point - collect all branches
                sub_branch_visited = visited.copy()
                for branch_key, next_workflow_node in next_nodes.items():
                    branch_target = next_workflow_node.id
                    sub_branch_label = BranchKeyNormalizer.normalize_to_capitalized(branch_key)
                    sub_branch_chain = self._traverse_branch(
                        branch_target,
                        sub_branch_visited.copy(),
                        sub_branch_label
                    )
                    # Add nodes maintaining order
                    for node_id in sub_branch_chain:
                        if node_id not in branch_chain:
                            branch_chain.append(node_id)
                        sub_branch_visited.add(node_id)
                break
            else:
                # Single edge - continue
                current_id = list(next_nodes.values())[0].id
        
        return branch_chain
    
    def _validate_and_add_node(self, node_id: str, visited: Set[str], chain: List[str]) -> bool:
        """
        Validate node existence, check for cycles, and add to chain.
        
        Args:
            node_id: ID of the node to validate and add
            visited: Set of already visited node IDs
            chain: List to add the node ID to
            
        Returns:
            True if node was successfully added, False if validation failed
        """
        # Check if node exists
        if not self.workflow_graph.get_node(node_id):
            logger.warning(f"[GraphTraverser] Warning: Node {node_id} referenced in edges but not found")
            return False
        
        # Check for cycles
        if node_id in visited:
            logger.warning(f"[GraphTraverser] Warning: Cycle detected at node {node_id}, stopping traversal")
            return False
        
        # Add to chain
        chain.append(node_id)
        visited.add(node_id)
        return True
    
    def _is_non_blocking_node(self, node_id: str) -> bool:
        """
        Check if a node is a NonBlockingNode.
        
        Args:
            node_id: ID of the node to check
            
        Returns:
            True if the node is a NonBlockingNode, False otherwise
        """
        base_node = self.workflow_graph.get_base_node(node_id)
        return base_node is not None and isinstance(base_node, NonBlockingNode)
