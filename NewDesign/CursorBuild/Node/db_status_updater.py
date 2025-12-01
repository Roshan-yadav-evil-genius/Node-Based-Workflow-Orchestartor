"""
Non-blocking node that updates job status in a database.
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import NonBlockingNode


class DBStatusUpdater(NonBlockingNode):
    """
    Non-blocking node that simulates updating job status in a database.
    
    Simulates the process of updating a database record.
    In a real implementation, this would execute actual SQL UPDATE queries.
    """
    
    def __init__(self, node_config: NodeConfig):
        """Initialize DB Status Updater node."""
        super().__init__(node_config)
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the status update by simulating a database update operation.
        
        Args:
            node_data: Input data containing job information
            
        Returns:
            NodeData: Output data with update status
        """
        # Simulate DB update delay
        delay = random.uniform(0.3, 0.6)
        await asyncio.sleep(delay)
        
        # Generate mock update result
        job_id = node_data.get("job_id", "unknown")
        new_status = "notified"  # Status after sending to Telegram
        
        # Simulate database update
        update_result = {
            "job_id": job_id,
            "old_status": "pending",
            "new_status": new_status,
            "updated_at": asyncio.get_event_loop().time(),
            "rows_affected": 1
        }
        
        # Add update result to output
        output_data = node_data.copy()
        output_data.set("db_update_result", update_result)
        output_data.set("job_status", new_status)
        output_data.metadata["db_updated"] = True
        output_data.metadata["update_timestamp"] = asyncio.get_event_loop().time()
        
        return output_data
