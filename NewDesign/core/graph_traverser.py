from typing import List, Optional, Tuple, Set
import structlog
from Nodes.Core.BaseNode import BaseNode
from Nodes.Core.BaseNode import ProducerNode, NonBlockingNode
from core.graph import WorkflowGraph
from core.workflow_node import WorkflowNode

logger = structlog.get_logger(__name__)


class GraphTraverser:
    """
    Handles all graph traversal operations.
    Follows Single Responsibility Principle - only handles traversal and querying.
    """

    def __init__(self, graph: WorkflowGraph):
        """
        Initialize GraphTraverser with a WorkflowGraph instance.

        Args:
            graph: WorkflowGraph instance to traverse
        """
        self.graph = graph

    def get_producer_nodes(self) -> List[WorkflowNode]:
        """
        Get all producer WorkflowNodes.

        Returns:
            List of producer WorkflowNodes
        """
        return [self.graph.node_map[node_id] for node_id in self.producer_node_ids]

    @property
    def producer_node_ids(self) -> List[str]:
        """
        Get all producer node IDs.

        Returns:
            List of producer node IDs
        """
        return [
            node_id
            for node_id, node_instance in self.graph.node_map.items()
            if isinstance(node_instance.instance, ProducerNode)
        ]

    def get_first_node_id(self) -> Optional[str]:
        """
        Get the ID of the first node in the graph.
        A first node is defined as a node with no incoming edges (root node).
        If no such node exists, returns the first producer node ID.

        Returns:
            ID of the first node, or None if graph is empty
        """
        if not self.graph.node_map:
            return None

        # Find all nodes that are targets of edges (have incoming edges)
        # MULTIPLE BRANCH SUPPORT: Must iterate through lists because multiple nodes
        # can point to the same target node through different branches
        nodes_with_incoming_edges = set()
        
        # OUTER LOOP: Iterate through all nodes in the graph
        for node in self.graph.node_map.values():
            # MIDDLE LOOP: Iterate through all branch keys (e.g., "default", "yes", "no")
            for next_nodes_list in node.next.values():
                # INNER LOOP: Iterate through all nodes in each branch list
                # REASON: A target node can appear in multiple branch lists, and we need
                # to find all nodes that have incoming edges (are targets of any branch)
                for next_node in next_nodes_list:
                    nodes_with_incoming_edges.add(next_node.id)

        # Find nodes with no incoming edges (root nodes)
        root_nodes = [
            node_id
            for node_id in self.graph.node_map.keys()
            if node_id not in nodes_with_incoming_edges
        ]

        # Return first root node if exists
        if root_nodes:
            return root_nodes[0]

        # If no root nodes, return first producer node
        producer_ids = self.producer_node_ids
        if producer_ids:
            return producer_ids[0]

        # If no producer nodes, return first node in node_map
        return list(self.graph.node_map.keys())[0] if self.graph.node_map else None

    def find_non_blocking_nodes(self) -> List[WorkflowNode]:
        """
        Find all non-blocking nodes.

        Returns:
            List of non-blocking WorkflowNodes
        """
        non_blocking_nodes = []
        for workFlowNodeId, workflowNode in self.graph.node_map.items():
            if isinstance(workflowNode.instance, NonBlockingNode):
                non_blocking_nodes.append(workflowNode)
        return non_blocking_nodes

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
                logger.warning(
                    f"No ending NonBlockingNode found for producer {producer_node.id}"
                )
        return loops

    def _find_ending_node_from_producer(
        self, producer_node: WorkflowNode
    ) -> Optional[WorkflowNode]:
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

    def _traverse_to_ending_node(
        self, current_node: WorkflowNode, visited: Set[str]
    ) -> Optional[WorkflowNode]:
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
            logger.warning(
                f"Cycle detected at node {current_node.id}, stopping traversal"
            )
            return None

        visited.add(current_node.id)

        # Get all next nodes
        next_nodes = current_node.next
        if not next_nodes:
            return None

        # MULTIPLE BRANCH SUPPORT: Check all branches to find NonBlockingNode
        # Must iterate through lists because multiple branches can exist per key
        # OUTER LOOP: Iterate through all branch keys (e.g., "default", "yes", "no")
        for next_nodes_list in next_nodes.values():
            # INNER LOOP: Iterate through all nodes in each branch list
            # REASON: Traverse all paths to find ending NonBlockingNode
            # Any branch that leads to a NonBlockingNode is valid
            for next_workflow_node in next_nodes_list:
                ending_node = self._traverse_to_ending_node(
                    next_workflow_node, visited.copy()
                )
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

    def build_chain_from_start_to_end(
        self, start_node: WorkflowNode, end_node: WorkflowNode
    ) -> List[BaseNode]:
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

            # MULTIPLE BRANCH SUPPORT: When multiple branch keys exist, collect from all
            if len(next_nodes) > 1:
                all_branch_nodes: Set[str] = set()
                # OUTER LOOP: Iterate through all branch keys
                for next_nodes_list in next_nodes.values():
                    # INNER LOOP: Iterate through all nodes in each branch list
                    # REASON: Must traverse all branches to collect all nodes in all paths
                    for next_workflow_node in next_nodes_list:
                        branch_chain = self._traverse_branch_to_end(
                            next_workflow_node, end_node, visited.copy()
                        )
                        # Collect all node IDs from this branch path
                        for node_id in branch_chain:
                            all_branch_nodes.add(node_id)
                            visited.add(node_id)

                # Add all branch nodes to chain (deduplicated via set)
                for node_id in all_branch_nodes:
                    node = self.graph.get_node(node_id)
                    if node and node.instance not in chain:
                        chain.append(node.instance)

                # After processing all branches, we should have reached end
                break
            else:
                # SINGLE BRANCH CASE: Backward compatible behavior
                # Get first node from first (and only) list
                # This maintains compatibility with old single-node structure
                first_list = list(next_nodes.values())[0] if next_nodes else []
                if not first_list:
                    break
                next_workflow_node = first_list[0]

                # Check if this is the end node
                if next_workflow_node.id == end_node.id:
                    chain.append(next_workflow_node.instance)
                    break

                # Check for cycles
                if next_workflow_node.id in visited:
                    logger.warning(
                        f"Cycle detected at node {next_workflow_node.id}"
                    )
                    break

                visited.add(next_workflow_node.id)
                chain.append(next_workflow_node.instance)
                current = next_workflow_node

        return chain

    def _traverse_branch_to_end(
        self, start_node: WorkflowNode, end_node: WorkflowNode, visited: Set[str]
    ) -> List[str]:
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

            # MULTIPLE BRANCH SUPPORT: When multiple branch keys exist, traverse all
            if len(next_nodes) > 1:
                # OUTER LOOP: Iterate through all branch keys
                for next_nodes_list in next_nodes.values():
                    # INNER LOOP: Iterate through all nodes in each branch list
                    # REASON: Recursively traverse all branches to find end node
                    # Each branch path is explored independently
                    for next_workflow_node in next_nodes_list:
                        sub_branch = self._traverse_branch_to_end(
                            next_workflow_node, end_node, visited.copy()
                        )
                        # Extend chain with all nodes from this branch path
                        branch_chain.extend(sub_branch)
                break
            else:
                # SINGLE BRANCH CASE: Backward compatible behavior
                # Get first node from first (and only) list
                # This maintains compatibility with old single-node structure
                first_list = list(next_nodes.values())[0] if next_nodes else []
                if first_list:
                    current = first_list[0]
                else:
                    break

        return branch_chain

