"""
Base Node class defining the contract for all node types.
Single Responsibility: Define the interface and contract for all nodes.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class Node(ABC):
    """
    Abstract base class for all workflow nodes.
    
    All nodes must implement:
    - run(): Execute the node's logic synchronously
    - identifier: Unique identifier for the node
    - label: Human-readable label
    - description: Description of what the node does
    """

    @abstractmethod
    def run(self, data: Any = None) -> Any:
        """
        Execute the node's logic synchronously.
        
        Args:
            data: Input data for the node (None for producer nodes)
            
        Returns:
            Output data from the node (None if no output)
        """
        pass

    @property
    @abstractmethod
    def identifier(self) -> str:
        """
        Get the unique identifier for this node.
        
        Returns:
            str: A unique identifier string for the node.
        """
        pass

    @property
    @abstractmethod
    def label(self) -> str:
        """
        Get the display label for this node.
        
        Returns:
            str: A human-readable label for the node.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get the description for this node.
        
        Returns:
            str: A description explaining what this node does.
        """
        pass

