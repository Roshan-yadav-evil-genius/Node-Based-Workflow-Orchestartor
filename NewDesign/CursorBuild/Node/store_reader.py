"""
Blocking node that reads data from a Store (simulated).
"""

import asyncio
import random

from domain import NodeConfig, NodeData
from nodes import BlockingNode


class StoreReader(BlockingNode):
    """
    Blocking node that simulates reading data from a Store.
    
    In a real implementation, this would read from an actual data store.
    For simulation, it returns the input data with a delay.
    """
    
    def __init__(self, node_config: NodeConfig):
        """Initialize Store Reader node."""
        super().__init__(node_config)
    
    async def execute(self, node_data: NodeData) -> NodeData:
        """
        Execute the store reader by simulating a read operation.
        
        Args:
            node_data: Input data (typically from Store node)
            
        Returns:
            NodeData: Data read from store (simulated)
        """
        # Simulate read delay
        delay = random.uniform(0.3, 0.7)
        await asyncio.sleep(delay)
        
        # In simulation, just return the data (in real implementation, would read from store)
        # Add metadata to indicate it was read from store
        node_data.metadata["read_from_store"] = True
        node_data.metadata["store_timestamp"] = asyncio.get_event_loop().time()
        
        return node_data
