from abc import ABC, abstractmethod


class BaseNodeProperty(ABC):
    """
    Abstract base class for node metadata properties.
    
    This class defines the interface for node identification and display
    properties. Subclasses must implement all abstract properties.
    """
    
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

    @property
    @abstractmethod
    def icon(self) -> str:
        """
        Get the icon identifier for this node.
        
        Returns:
            str: An icon identifier or path for displaying the node.
        """
        pass

