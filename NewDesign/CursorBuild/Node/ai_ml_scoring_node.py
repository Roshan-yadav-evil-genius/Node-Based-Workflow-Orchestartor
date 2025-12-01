"""
Non-blocking node that performs AI/ML opportunity scoring.
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import NonBlockingNode


class AIMLScoringNode(NonBlockingNode):
    """
    Non-blocking node that simulates AI/ML opportunity scoring.
    
    Generates a mock score (0.0-1.0) based on job characteristics.
    In a real implementation, this would use actual ML models.
    """
    
    def __init__(self, node_config: NodeConfig):
        """Initialize AI/ML Scoring node."""
        super().__init__(node_config)
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the scoring by generating a mock opportunity score.
        
        Args:
            node_data: Input data containing job information
            
        Returns:
            NodeData: Output data with score added
        """
        # Simulate scoring delay (ML inference time)
        delay = random.uniform(0.8, 1.5)
        await asyncio.sleep(delay)
        
        # Generate mock score based on job characteristics
        # Python jobs tend to score higher
        is_python = node_data.get("is_python_job", False)
        
        if is_python:
            # Python jobs score between 0.6-1.0
            score = random.uniform(0.6, 1.0)
        else:
            # Other jobs score between 0.2-0.8
            score = random.uniform(0.2, 0.8)
        
        # Add score to output
        output_data = node_data.copy()
        output_data.set("score", score)
        output_data.metadata["score"] = score
        output_data.metadata["scoring_timestamp"] = asyncio.get_event_loop().time()
        output_data.metadata["scoring_model"] = "mock_ai_model_v1"
        
        return output_data
