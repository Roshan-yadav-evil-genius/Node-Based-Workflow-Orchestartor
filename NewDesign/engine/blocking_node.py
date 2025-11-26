"""
Blocking Node implementation.
Single Responsibility: Execute synchronous work that blocks upstream.
"""

from abc import abstractmethod
from typing import Any
from .base_node import Node


class BlockingNode(Node):
    """
    Blocking Node executes work that must be completed before upstream nodes
    (like the Producer) continue.
    
    Execution Behavior:
    - Triggered when new data arrives
    - Runs synchronously and passes output to the next node
    - Waits for entire downstream chain to complete before returning control
    - Forms strict synchronous paths within the workflow
    """

    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Process the input data synchronously.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed output data
        """
        pass

    def run(self, data: Any = None) -> Any:
        """
        Execute the blocking node by processing the data.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed output data
        """
        if data is None:
            raise ValueError("BlockingNode requires input data")
        return self.process(data)

