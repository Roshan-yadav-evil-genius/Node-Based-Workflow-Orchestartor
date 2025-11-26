"""
Non-Blocking Node implementation.
Single Responsibility: Execute work without blocking upstream.
"""

from abc import abstractmethod
from typing import Any
from .base_node import Node


class NonBlockingNode(Node):
    """
    Non-Blocking Node performs computation or transformation but does not
    force the Producer to wait for downstream operations.
    
    Execution Behavior:
    - Runs synchronously internally
    - Returns control immediately to Producer after task completion
    - Downstream operations run in separate loops or independent systems
    - Useful for creating async boundaries within the workflow
    """

    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Process the input data synchronously.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed output data (may be used by downstream nodes)
        """
        pass

    def run(self, data: Any = None) -> Any:
        """
        Execute the non-blocking node by processing the data.
        Note: The engine handles returning control immediately to the producer.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed output data
        """
        if data is None:
            raise ValueError("NonBlockingNode requires input data")
        return self.process(data)

