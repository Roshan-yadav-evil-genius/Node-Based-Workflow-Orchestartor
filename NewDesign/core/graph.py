from typing import Dict, List, Optional, Tuple, Set
import structlog
from Nodes.Core.BaseNode import BaseNode
from Nodes.Core.BaseNode import ProducerNode, NonBlockingNode
from core.workflow_node import WorkflowNode

logger = structlog.get_logger(__name__)


class WorkflowGraph:
    """
    Class to hold workflow graph structure with linked WorkflowNode instances.
    Supports incremental building and provides utility methods for traversal and querying.
    """

    def __init__(self):
        self.node_map: Dict[str, WorkflowNode] = {}  # Linked graph structure for traversal

    def add_node(self, workflow_node: WorkflowNode):
        """
        Add a node to the graph.
        
        Args:
            workflow_node: WorkflowNode instance to add
        """
        if workflow_node.id in self.node_map:
            raise ValueError(f"Node with id '{workflow_node.id}' already exists in the graph")
        
        self.node_map[workflow_node.id] = workflow_node

    def add_node_at_end_of(self, node_id: str, workflow_node: WorkflowNode, key: str = "default"):
        """
        Add a node at the end of a specific node.
        
        Args:
            node_id: ID of the node to add after
            workflow_node: WorkflowNode instance to add
            key: Key to use for the connection (default: "default")
        """
        if node_id not in self.node_map:
            raise ValueError(f"Node with id '{node_id}' not found in the graph")
        
        # Add the new node first
        self.add_node(workflow_node)
        
        # Connect it to the specified node
        self.node_map[node_id].add_next(workflow_node, key)

    def connect_nodes(self, from_id: str, to_id: str, key: str = "default"):
        """
        Connect two existing nodes.
        
        Args:
            from_id: ID of the source node
            to_id: ID of the target node
            key: Key to use for the connection (default: "default")
        """
        if from_id not in self.node_map:
            raise ValueError(f"Node with id '{from_id}' not found in the graph")
        if to_id not in self.node_map:
            raise ValueError(f"Node with id '{to_id}' not found in the graph")
        
        self.node_map[from_id].add_next(self.node_map[to_id], key)


    def get_producer_nodes(self) -> List[WorkflowNode]:
        """
        Get all producer WorkflowNodes.
        
        Returns:
            List of producer WorkflowNodes
        """
        return [self.node_map[node_id] for node_id in self.producer_node_ids]
    
    @property
    def producer_node_ids(self) -> List[str]:
        """
        Get all producer node IDs.
        
        Returns:
            List of producer node IDs
        """
        return [node_id for node_id, node_instance in self.node_map.items() if isinstance(node_instance.instance, ProducerNode)]

    def get_first_node_id(self) -> Optional[str]:
        """
        Get the ID of the first node in the graph.
        A first node is defined as a node with no incoming edges (root node).
        If no such node exists, returns the first producer node ID.
        
        Returns:
            ID of the first node, or None if graph is empty
        """
        if not self.node_map:
            return None
        
        # Find all nodes that are targets of edges (have incoming edges)
        nodes_with_incoming_edges = set()
        for node in self.node_map.values():
            for next_node in node.next.values():
                nodes_with_incoming_edges.add(next_node.id)
        
        # Find nodes with no incoming edges (root nodes)
        root_nodes = [node_id for node_id in self.node_map.keys() if node_id not in nodes_with_incoming_edges]
        
        # Return first root node if exists
        if root_nodes:
            return root_nodes[0]
        
        # If no root nodes, return first producer node
        producer_ids = self.producer_node_ids
        if producer_ids:
            return producer_ids[0]
        
        # If no producer nodes, return first node in node_map
        return list(self.node_map.keys())[0] if self.node_map else None

    def get_all_next(self, node_id: str) -> Dict[str, WorkflowNode]:
        """
        Get all next nodes.
        
        Args:
            node_id: ID of the source node
            
        Returns:
            Dictionary of key -> WorkflowNode mappings, or empty dict if none
        """
        if node_id not in self.node_map:
            return {}
        
        node = self.node_map[node_id]
        return node.next.copy()

    def find_non_blocking_nodes(self) -> List[WorkflowNode]:
        """
        Find all non-blocking nodes.
        
        Returns:
            List of non-blocking WorkflowNodes
        """
        non_blocking_nodes = []
        for workFlowNodeId, workflowNode in self.node_map.items():
            if isinstance(workflowNode.instance, NonBlockingNode):
                non_blocking_nodes.append(workflowNode)
        return non_blocking_nodes

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """
        Get WorkflowNode by ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            WorkflowNode or None if not found
        """
        return self.node_map.get(node_id)

    def get_node_instance(self, node_id: str) -> Optional[BaseNode]:
        """
        Get BaseNode instance by ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            BaseNode or None if not found
        """
        workflow_node = self.node_map.get(node_id)
        return workflow_node.instance if workflow_node else None

    def find_loops(self) -> List[Tuple[WorkflowNode, WorkflowNode]]:
        """
        Find all loops starting from ProducerNodes.
        
        Returns:
            List of tuples: (starting_producer_workflow_node, ending_non_blocking_workflow_node) for each loop
        """
        loops = []
        for producer_node in self.get_producer_nodes():
            ending_node = self._find_ending_node_from_producer(producer_node)
            if ending_node:
                loops.append((producer_node, ending_node))
            else:
                logger.warning(f"[WorkflowGraph] No ending NonBlockingNode found for producer {producer_node.id}")
        return loops

    def _find_ending_node_from_producer(self, producer_node: WorkflowNode) -> Optional[WorkflowNode]:
        """
        Traverse from a producer WorkflowNode until a NonBlockingNode is reached.
        Handles conditional branches by following all paths until NonBlockingNode is found.
        
        Args:
            producer_node: Producer WorkflowNode to start traversal from
            
        Returns:
            Ending NonBlockingNode WorkflowNode, or None if not found
        """
        visited: Set[str] = set()
        return self._traverse_to_ending_node(producer_node, visited)

    def _traverse_to_ending_node(self, current_node: WorkflowNode, visited: Set[str]) -> Optional[WorkflowNode]:
        """
        Recursively traverse from current node to find ending NonBlockingNode.
        Handles branching by checking all paths.
        
        Args:
            current_node: Current WorkflowNode to check
            visited: Set of visited node IDs to prevent cycles
            
        Returns:
            NonBlockingNode WorkflowNode if found, None otherwise
        """
        # Check if current node is NonBlockingNode first (before cycle check)
        if self._is_non_blocking_node(current_node):
            return current_node
        
        # Check for cycles
        if current_node.id in visited:
            logger.warning(f"[WorkflowGraph] Cycle detected at node {current_node.id}, stopping traversal")
            return None
        
        visited.add(current_node.id)
        
        # Get all next nodes
        next_nodes = current_node.next
        if not next_nodes:
            return None
        
        # If multiple branches, check all of them
        for next_workflow_node in next_nodes.values():
            ending_node = self._traverse_to_ending_node(next_workflow_node, visited.copy())
            if ending_node:
                return ending_node
        
        return None

    def _is_non_blocking_node(self, workflow_node: WorkflowNode) -> bool:
        """
        Check if a WorkflowNode's instance is a NonBlockingNode.
        
        Args:
            workflow_node: WorkflowNode to check
            
        Returns:
            True if the node is a NonBlockingNode, False otherwise
        """
        return isinstance(workflow_node.instance, NonBlockingNode)

    def build_chain_from_start_to_end(self, start_node: WorkflowNode, end_node: WorkflowNode) -> List[BaseNode]:
        """
        Build a chain of BaseNode instances from start to end WorkflowNode.
        Traverses the graph following next connections, collecting all nodes until end is reached.
        Handles branches by collecting nodes from all paths.
        
        Args:
            start_node: Starting WorkflowNode (producer)
            end_node: Ending WorkflowNode (NonBlockingNode)
            
        Returns:
            List of BaseNode instances from start to end (excluding start, including end)
        """
        chain: List[BaseNode] = []
        visited: Set[str] = {start_node.id}
        current = start_node
        
        while current and current.id != end_node.id:
            next_nodes = current.next
            if not next_nodes:
                break
            
            # If multiple branches, collect from all branches
            if len(next_nodes) > 1:
                all_branch_nodes: Set[str] = set()
                for next_workflow_node in next_nodes.values():
                    branch_chain = self._traverse_branch_to_end(next_workflow_node, end_node, visited.copy())
                    for node_id in branch_chain:
                        all_branch_nodes.add(node_id)
                        visited.add(node_id)
                
                # Add all branch nodes to chain
                for node_id in all_branch_nodes:
                    node = self.get_node(node_id)
                    if node and node.instance not in chain:
                        chain.append(node.instance)
                
                # After processing branches, we should have reached end
                break
            else:
                # Single edge - follow normally
                next_workflow_node = list(next_nodes.values())[0]
                
                # Check if this is the end node
                if next_workflow_node.id == end_node.id:
                    chain.append(next_workflow_node.instance)
                    break
                
                # Check for cycles
                if next_workflow_node.id in visited:
                    logger.warning(f"[WorkflowGraph] Cycle detected at node {next_workflow_node.id}")
                    break
                
                visited.add(next_workflow_node.id)
                chain.append(next_workflow_node.instance)
                current = next_workflow_node
        
        return chain

    def _traverse_branch_to_end(self, start_node: WorkflowNode, end_node: WorkflowNode, visited: Set[str]) -> List[str]:
        """
        Traverse a branch from start node until end node is reached.
        
        Args:
            start_node: Starting WorkflowNode
            end_node: Target ending WorkflowNode
            visited: Set of visited node IDs
            
        Returns:
            List of node IDs in this branch path
        """
        branch_chain: List[str] = []
        current = start_node
        
        while current:
            # Check if we reached the end
            if current.id == end_node.id:
                branch_chain.append(current.id)
                break
            
            # Check for cycles
            if current.id in visited:
                break
            
            visited.add(current.id)
            branch_chain.append(current.id)
            
            # Get next nodes
            next_nodes = current.next
            if not next_nodes:
                break
            
            # If multiple edges, recursively traverse all branches
            if len(next_nodes) > 1:
                for next_workflow_node in next_nodes.values():
                    sub_branch = self._traverse_branch_to_end(next_workflow_node, end_node, visited.copy())
                    branch_chain.extend(sub_branch)
                break
            else:
                current = list(next_nodes.values())[0]
        
        return branch_chain

