"""
Producer node that simulates monitoring freelance jobs using Playwright.
"""

import asyncio
import random
from typing import Dict, Any

from domain import NodeConfig, NodeData
from nodes import ProducerNode


class PlaywrightFreelanceJobMonitorProducer(ProducerNode):
    """
    Producer node that simulates monitoring freelance job platforms.
    
    Generates mock job data with random properties including whether
    the job is Python-related.
    """
    
    def __init__(self, node_config: NodeConfig):
        """Initialize Playwright Freelance Job Monitor Producer."""
        super().__init__(node_config)
        self._job_counter = 0
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the producer by generating mock job data.
        
        Args:
            node_data: Input data (typically empty for producers)
            
        Returns:
            NodeData: Output data containing mock job information
        """
        # Simulate monitoring delay
        delay = random.uniform(0.5, 1.0)
        await asyncio.sleep(delay)
        
        # Generate mock job data
        self._job_counter += 1
        job_id = f"job_{self._job_counter:04d}"
        
        # Randomly determine if it's a Python job (30% chance)
        is_python_job = random.random() < 0.3
        
        # Generate job title based on type
        if is_python_job:
            titles = [
                "Python Developer Needed",
                "Django Backend Developer",
                "Python Data Scientist",
                "Flask API Developer",
                "Python Automation Engineer"
            ]
        else:
            titles = [
                "JavaScript Developer",
                "React Frontend Developer",
                "Full Stack Engineer",
                "Mobile App Developer",
                "DevOps Engineer"
            ]
        
        job_title = random.choice(titles)
        
        # Generate mock job description
        job_description = (
            f"Looking for an experienced developer to work on {job_title.lower()} project. "
            f"Must have strong problem-solving skills and ability to work independently. "
            f"Remote position with flexible hours."
        )
        
        # Create output data
        output_data = NodeData()
        output_data.set("job_id", job_id)
        output_data.set("job_title", job_title)
        output_data.set("job_description", job_description)
        output_data.set("is_python_job", is_python_job)
        output_data.set("timestamp", asyncio.get_event_loop().time())
        
        # Add metadata
        output_data.metadata["source"] = "playwright_monitor"
        output_data.metadata["iteration"] = self._job_counter
        
        return output_data
