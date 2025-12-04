import structlog
from core.PostProcessing import PostProcessor

logger = structlog.get_logger(__name__)


class NodeValidator(PostProcessor):
    """
    Handles validation of all nodes in the workflow graph.
    Follows Single Responsibility Principle - only handles node validation.
    """

    def execute(self) -> None:
        """
        Validate all nodes in the graph by calling their ready() method.
        Raises ValueError if any node is not ready.
        """
        logger.info("Validating all nodes in workflow...")
        
        errors_by_node = {}
        for node_id, workflow_node in self.graph.node_map.items():
            node_errors = workflow_node.instance.ready()
            if node_errors:
                errors_by_node[node_id] = node_errors
        
        if errors_by_node:
            error_messages = []
            for node_id, errors in errors_by_node.items():
                error_list = ', '.join(errors.values())
                error_messages.append(f"Node '{node_id}': {error_list}")
            
            error_text = "Workflow validation failed:\n" + "\n".join(error_messages)
            logger.error(error_text)
            raise ValueError(error_text)
        
        logger.info("All nodes validated successfully.")
