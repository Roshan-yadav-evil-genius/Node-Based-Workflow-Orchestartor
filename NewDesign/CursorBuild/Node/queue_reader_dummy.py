"""
Dummy blocking node that simulates reading from a Queue.
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import BlockingNode


class QueueReaderDummy(BlockingNode):
    """
    Dummy blocking node that simulates reading from a Queue.
    
    In a real implementation, this would use QueueReader that pops from Redis.
    For simulation, it returns mock data with a delay.
    """
    
    def __init__(self, node_config: NodeConfig, queue_name: str = "default"):
        """
        Initialize Queue Reader Dummy node.
        
        Args:
            node_config: Static configuration for this node
            queue_name: Name of the queue (for simulation purposes)
        """
        super().__init__(node_config)
        self._queue_name = queue_name
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the queue reader by simulating a pop operation.
        
        Args:
            node_data: Input data (typically empty for queue readers)
            
        Returns:
            NodeData: Data popped from queue (simulated)
        """
        # Simulate queue pop delay (blocking wait)
        delay = random.uniform(0.5, 1.0)
        await asyncio.sleep(delay)
        
        # In simulation, generate mock data from queue
        # In real implementation, would pop from Redis queue
        output_data = NodeData()
        
        # If input has data, use it; otherwise generate mock
        if node_data.data:
            output_data = node_data.copy()
        else:
            output_data.set("job_id", node_data.get("job_id", "queued_job_001"))
            output_data.set("job_title", node_data.get("job_title", "Queued Job"))
            output_data.set("score", node_data.get("score", 0.85))
        
        output_data.metadata["read_from_queue"] = True
        output_data.metadata["queue_name"] = self._queue_name
        output_data.metadata["queue_timestamp"] = asyncio.get_event_loop().time()
        
        return output_data
