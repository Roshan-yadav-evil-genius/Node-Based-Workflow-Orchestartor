from abc import ABC, abstractmethod
from typing import Optional

from .Data import PoolType
from ...Form.Core.BaseForm import BaseForm


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
    
    @property
    def form(self) -> Optional[BaseForm]:
        """
        Get the associated form for this node.
        Default implementation returns None.

        Returns:
            BaseForm: An instance of the form corresponding to this node, or None.
        """
        return None
