"""
Conditional node that checks if a score exceeds a threshold.
"""

from domain import NodeConfig, NodeData
from Node.conditional_node import ConditionalNode


class IfScoreThresholdNode(ConditionalNode):
    """
    Conditional node that checks if a score exceeds a threshold (default 0.8).
    
    Evaluates the 'score' field in the input data and routes to different
    paths based on whether it exceeds the threshold.
    """
    
    def __init__(self, node_config: NodeConfig, threshold: float = 0.8):
        """
        Initialize IF Score Threshold node.
        
        Args:
            node_config: Static configuration for this node
            threshold: Score threshold (default: 0.8)
        """
        super().__init__(
            node_config=node_config,
            condition_key="score_threshold_result",
            true_label="Yes",
            false_label="No"
        )
        self._threshold = threshold
    
    def evaluate_condition(self, node_data: NodeData) -> bool:
        """
        Check if score exceeds threshold.
        
        Args:
            node_data: Input data containing score information
            
        Returns:
            bool: True if score > threshold, False otherwise
        """
        score = node_data.get("score", 0.0)
        
        # Try to get score from metadata if not in data
        if score == 0.0:
            score = node_data.metadata.get("score", 0.0)
        
        return float(score) > self._threshold
