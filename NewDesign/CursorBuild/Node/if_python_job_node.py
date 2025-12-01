"""
Conditional node that checks if a job is Python-related.
"""

from domain import NodeConfig, NodeData
from Node.conditional_node import ConditionalNode


class IfPythonJobNode(ConditionalNode):
    """
    Conditional node that checks if a job is Python-related.
    
    Evaluates the 'is_python_job' field in the input data and routes
    to different paths based on the result.
    """
    
    def __init__(self, node_config: NodeConfig):
        """Initialize IF Python Job node."""
        super().__init__(
            node_config=node_config,
            condition_key="is_python_job_result",
            true_label="Yes",
            false_label="No"
        )
    
    def evaluate_condition(self, node_data: NodeData) -> bool:
        """
        Check if the job is Python-related.
        
        Args:
            node_data: Input data containing job information
            
        Returns:
            bool: True if job is Python-related, False otherwise
        """
        # Check if is_python_job flag exists in data
        is_python = node_data.get("is_python_job", False)
        
        # Also check job title/description for Python keywords
        if not is_python:
            title = node_data.get("job_title", "").lower()
            description = node_data.get("job_description", "").lower()
            is_python = "python" in title or "python" in description
        
        return bool(is_python)
