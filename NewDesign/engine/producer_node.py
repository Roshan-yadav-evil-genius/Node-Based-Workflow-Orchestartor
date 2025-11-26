"""
Producer Node implementation.
Single Responsibility: Generate work items in a loop.
"""

from abc import abstractmethod
from typing import Any, Optional
from .base_node import Node


class ProducerNode(Node):
    """
    Producer Node starts a workflow loop by continuously generating or fetching
    new units of work. It controls when the next iteration of the loop begins.
    
    Execution Behavior:
    - Executes synchronously
    - Continues to next iteration only after all connected Blocking Nodes complete
    - Immediately regains control from Non-Blocking Nodes
    """

    @abstractmethod
    def produce(self) -> Optional[Any]:
        """
        Generate or fetch a new unit of work.
        
        Returns:
            A work item if available, None if no work is available
        """
        pass

    def run(self, data: Any = None) -> Optional[Any]:
        """
        Execute the producer by calling produce().
        
        Args:
            data: Ignored for producer nodes (always None)
            
        Returns:
            The produced work item, or None if no work available
        """
        return self.produce()

