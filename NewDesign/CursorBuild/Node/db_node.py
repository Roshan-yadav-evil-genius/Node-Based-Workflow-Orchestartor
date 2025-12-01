"""
Non-blocking node that writes data to a Database (simulated).
Uses QueueNode pattern for consistency.
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import NonBlockingNode


class DBNode(NonBlockingNode):
    """
    Non-blocking node that simulates writing data to a Database.
    
    Follows the QueueNode pattern - writes data and returns immediately.
    In a real implementation, this would execute actual SQL INSERT queries.
    """
    
    def __init__(self, node_config: NodeConfig, table_name: str = "jobs"):
        """
        Initialize DB Node.
        
        Args:
            node_config: Static configuration for this node
            table_name: Name of the database table (for simulation purposes)
        """
        super().__init__(node_config)
        self._table_name = table_name
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the database write operation by simulating an INSERT.
        
        Args:
            node_data: Data to write to database
            
        Returns:
            NodeData: Returns the same data (no transformation)
        """
        # Simulate DB write delay
        delay = random.uniform(0.3, 0.6)
        await asyncio.sleep(delay)
        
        # In simulation, just add metadata (in real implementation, would execute SQL INSERT)
        job_id = node_data.get("job_id", "unknown")
        node_data.metadata["db_written"] = True
        node_data.metadata["table_name"] = self._table_name
        node_data.metadata["db_record_id"] = f"db_{job_id}"
        node_data.metadata["db_timestamp"] = asyncio.get_event_loop().time()
        
        return node_data
