from abc import ABC, abstractmethod

from .Data import PoolType


class BaseNodeProperty(ABC):
    """
    Abstract base class for node metadata properties.
    
    This class defines the interface for node identification and display
    properties. Subclasses must implement execution_pool and identifier.
    Other properties have default implementations for backward compatibility.
    """

    @property
    @abstractmethod
    def execution_pool(self) -> PoolType:
        """
        The preferred execution pool for this node.
        """
        pass

    @classmethod
    @abstractmethod
    def identifier(cls) -> str:
        """
        Return the node type identifier (kebab-case string).
        This identifier is used to map node types from workflow definitions to node classes.
        """
        pass

    @property
    def label(self) -> str:
        """
        Get the display label for this node.
        Default implementation returns the class name.
        
        Returns:
            str: A human-readable label for the node.
        """
        return self.__class__.__name__

    @property
    def description(self) -> str:
        """
        Get the description for this node.
        Default implementation returns empty string.
        
        Returns:
            str: A description explaining what this node does.
        """
        return ""

    @property
    def icon(self) -> str:
        """
        Get the icon identifier for this node.
        Default implementation returns empty string.
        
        Returns:
            str: An icon identifier or path for displaying the node.
        """
        return ""
