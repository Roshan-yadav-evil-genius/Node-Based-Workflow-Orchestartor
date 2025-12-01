"""
Non-blocking node that writes data to a Store (simulated).
Uses QueueNode pattern for consistency.
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import NonBlockingNode


class StoreNode(NonBlockingNode):
    """
    Non-blocking node that simulates writing data to a Store.
    
    Follows the QueueNode pattern - writes data and returns immediately.
    In a real implementation, this would write to an actual data store.
    """
    
    def __init__(self, node_config: NodeConfig, store_name: str = "default_store"):
        """
        Initialize Store Node.
        
        Args:
            node_config: Static configuration for this node
            store_name: Name of the store (for simulation purposes)
        """
        super().__init__(node_config)
        self._store_name = store_name
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the store operation by simulating a write.
        
        Args:
            node_data: Data to store
            
        Returns:
            NodeData: Returns the same data (no transformation)
        """
        # Simulate store write delay
        delay = random.uniform(0.2, 0.5)
        await asyncio.sleep(delay)
        
        # In simulation, just add metadata (in real implementation, would write to store)
        node_data.metadata["stored"] = True
        node_data.metadata["store_name"] = self._store_name
        node_data.metadata["store_timestamp"] = asyncio.get_event_loop().time()
        
        return node_data
