"""
Non-blocking node that uses LLM to prepare job proposals.
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import NonBlockingNode


class LLMProposalPreparer(NonBlockingNode):
    """
    Non-blocking node that simulates LLM agent preparing job proposals.
    
    Generates mock proposal text based on job information.
    In a real implementation, this would use actual LLM APIs.
    """
    
    def __init__(self, node_config: NodeConfig):
        """Initialize LLM Proposal Preparer node."""
        super().__init__(node_config)
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the proposal preparation by generating mock proposal text.
        
        Args:
            node_data: Input data containing job information
            
        Returns:
            NodeData: Output data with proposal added
        """
        # Simulate LLM processing delay
        delay = random.uniform(1.0, 2.0)
        await asyncio.sleep(delay)
        
        # Generate mock proposal
        job_title = node_data.get("job_title", "the position")
        job_id = node_data.get("job_id", "unknown")
        
        proposal_text = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my strong interest in {job_title} (Job ID: {job_id}). "
            f"With my extensive experience in software development and passion for creating "
            f"high-quality solutions, I am confident that I would be a valuable addition to your team.\n\n"
            f"I have a proven track record of delivering successful projects and working "
            f"collaboratively with cross-functional teams. I am excited about the opportunity "
            f"to contribute to your organization's success.\n\n"
            f"Thank you for considering my application.\n\n"
            f"Best regards,\n"
            f"AI Agent"
        )
        
        # Add proposal to output
        output_data = node_data.copy()
        output_data.set("proposal_text", proposal_text)
        output_data.metadata["proposal_generated"] = True
        output_data.metadata["proposal_timestamp"] = asyncio.get_event_loop().time()
        output_data.metadata["llm_model"] = "mock_llm_gpt4"
        
        return output_data
