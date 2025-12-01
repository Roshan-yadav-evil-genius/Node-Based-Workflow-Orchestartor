"""
Dummy non-blocking node that writes data to a Queue (simulated).
Uses QueueNode pattern for consistency.
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import NonBlockingNode


class QueueNodeDummy(NonBlockingNode):
    """
    Dummy non-blocking node that simulates writing data to a Queue.
    
    Follows the QueueNode pattern - writes data and returns immediately.
    In a real implementation, this would use the actual QueueNode with Redis.
    """
    
    def __init__(self, node_config: NodeConfig, queue_name: str = "default_queue"):
        """
        Initialize Queue Node Dummy.
        
        Args:
            node_config: Static configuration for this node
            queue_name: Name of the queue (for simulation purposes)
        """
        super().__init__(node_config)
        self._queue_name = queue_name
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the queue operation by simulating a push.
        
        Args:
            node_data: Data to push to queue
            
        Returns:
            NodeData: Returns the same data (no transformation)
        """
        # Simulate queue push delay
        delay = random.uniform(0.2, 0.4)
        await asyncio.sleep(delay)
        
        # In simulation, just add metadata (in real implementation, would push to Redis queue)
        node_data.metadata["queued"] = True
        node_data.metadata["queue_name"] = self._queue_name
        node_data.metadata["queue_timestamp"] = asyncio.get_event_loop().time()
        
        return node_data
