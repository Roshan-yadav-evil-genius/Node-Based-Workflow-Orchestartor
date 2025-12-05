from typing import Optional
import structlog
from Nodes.Core.BaseNode import BaseNode
from Nodes.Node.System.QueueNode import QueueNode
from Nodes.Node.System.QueueReader import QueueReader
from core.workflow_node import WorkflowNode
from core.PostProcessing import PostProcessor

logger = structlog.get_logger(__name__)


class QueueMapper(PostProcessor):
    """
    Handles automatic queue name assignment for connected QueueNode-QueueReader pairs.
    Follows Single Responsibility Principle - only handles queue mapping logic.
    """

    def execute(self) -> None:
        """
        Process the graph and assign unique queue names to connected QueueNode-QueueReader pairs.
        """
        logger.info("Mapping queues for connected QueueNode-QueueReader pairs...")
        
        mapped_count = 0
        for node_id, workflow_node in self.graph.node_map.items():
            # Check if this node is a QueueNode
            if not self._is_queue_node(workflow_node.instance):
                continue
            
            # Iterate through all connected nodes
            for next_key, next_nodes_list in workflow_node.next.items():
                for next_node in next_nodes_list:
                    # Check if the connected node is a QueueReader
                    if self._is_queue_reader(next_node.instance):
                        # Generate unique queue name
                        queue_name = self._generate_queue_name(node_id, next_node.id)
                        
                        # Assign queue name to both nodes
                        self._assign_queue_name(workflow_node, next_node, queue_name)
                        mapped_count += 1
                        logger.info(
                            f"Auto-assigned queue name '{queue_name}' to QueueNode '{node_id}' and QueueReader '{next_node.id}'"
                        )
        
        logger.info(f"Queue mapping completed. Mapped {mapped_count} QueueNode-QueueReader pairs.")

    def _is_queue_node(self, node_instance: BaseNode) -> bool:
        """
        Check if node is QueueNode or a subclass.

        Args:
            node_instance: BaseNode instance to check

        Returns:
            True if node is QueueNode or subclass, False otherwise
        """
        return isinstance(node_instance, QueueNode)

    def _is_queue_reader(self, node_instance: BaseNode) -> bool:
        """
        Check if node is QueueReader or a subclass.

        Args:
            node_instance: BaseNode instance to check

        Returns:
            True if node is QueueReader or subclass, False otherwise
        """
        return isinstance(node_instance, QueueReader)

    def _generate_queue_name(self, source_id: str, target_id: str) -> str:
        """
        Generate unique queue name from source and target node IDs.

        Args:
            source_id: ID of the source QueueNode
            target_id: ID of the target QueueReader

        Returns:
            Unique queue name string
        """
        return f"queue_{source_id}_{target_id}"

    def _assign_queue_name(
        self, source_node: WorkflowNode, target_node: WorkflowNode, queue_name: str
    ) -> None:
        """
        Assign queue name to both source and target nodes' configs.

        Args:
            source_node: WorkflowNode instance (QueueNode)
            target_node: WorkflowNode instance (QueueReader)
            queue_name: Queue name to assign
        """
        # Ensure config.data exists for source node
        if source_node.instance.config.data is None:
            source_node.instance.config.data = {}

        # Ensure config.data exists for target node
        if target_node.instance.config.data is None:
            target_node.instance.config.data = {}

        # Only assign if not already set or is "default"
        if source_node.instance.config.data.get("queue_name") in (None, "default"):
            source_node.instance.config.data["queue_name"] = queue_name

        if target_node.instance.config.data.get("queue_name") in (None, "default"):
            target_node.instance.config.data["queue_name"] = queue_name
