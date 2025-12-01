"""
Blocking node that queries a database (simulated).
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import BlockingNode


class QueryDB(BlockingNode):
    """
    Blocking node that simulates querying a database.
    
    In a real implementation, this would execute actual SQL queries.
    For simulation, it returns mock query results with a delay.
    """
    
    def __init__(self, node_config: NodeConfig):
        """Initialize Query DB node."""
        super().__init__(node_config)
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the database query by simulating a query operation.
        
        Args:
            node_data: Input data containing query parameters
            
        Returns:
            NodeData: Query results (simulated)
        """
        # Simulate query delay
        delay = random.uniform(0.4, 0.8)
        await asyncio.sleep(delay)
        
        # In simulation, return mock query results
        # In real implementation, would execute SQL query
        output_data = node_data.copy()
        
        # Add mock query results
        job_id = node_data.get("job_id", "unknown")
        output_data.set("query_results", {
            "job_id": job_id,
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        })
        
        output_data.metadata["query_executed"] = True
        output_data.metadata["query_timestamp"] = asyncio.get_event_loop().time()
        
        return output_data
