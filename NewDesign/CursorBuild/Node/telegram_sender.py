"""
Non-blocking node that sends job information to a Telegram group.
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import NonBlockingNode


class TelegramSender(NonBlockingNode):
    """
    Non-blocking node that simulates sending job information to a Telegram group.
    
    Simulates the process of sending a message via Telegram API.
    In a real implementation, this would use actual Telegram Bot API.
    """
    
    def __init__(self, node_config: NodeConfig, group_id: str = "default_group"):
        """
        Initialize Telegram Sender node.
        
        Args:
            node_config: Static configuration for this node
            group_id: Telegram group ID (for simulation purposes)
        """
        super().__init__(node_config)
        self._group_id = group_id
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the Telegram sending by simulating message sending.
        
        Args:
            node_data: Input data containing job information
            
        Returns:
            NodeData: Output data with send status
        """
        # Simulate Telegram API delay
        delay = random.uniform(0.5, 1.0)
        await asyncio.sleep(delay)
        
        # Generate mock message
        job_id = node_data.get("job_id", "unknown")
        job_title = node_data.get("job_title", "Job Opportunity")
        
        message_text = (
            f"📢 New Job Opportunity\n\n"
            f"Title: {job_title}\n"
            f"Job ID: {job_id}\n"
            f"Status: Available for bidding\n\n"
            f"Check it out!"
        )
        
        # Simulate message sending
        message_id = f"msg_{random.randint(10000, 99999)}"
        
        # Add send status to output
        output_data = node_data.copy()
        output_data.set("telegram_message_id", message_id)
        output_data.set("telegram_message_text", message_text)
        output_data.set("telegram_group_id", self._group_id)
        output_data.metadata["telegram_sent"] = True
        output_data.metadata["telegram_timestamp"] = asyncio.get_event_loop().time()
        
        return output_data
