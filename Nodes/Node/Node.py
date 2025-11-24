from abc import abstractmethod
from typing import Dict, Any
from .BaseNodeProperty import BaseNodeProperty
from .BaseNodeForm import BaseNodeForm


class Node(BaseNodeProperty, BaseNodeForm):
    """
    Concrete base class that combines node properties and form functionality.
    
    This class inherits from both BaseNodeProperty and BaseNodeForm, combining
    node metadata management with form schema management. Subclasses should
    override the abstract methods to provide specific implementations.
    """
    
    def __init__(self):
        """
        Initialize the Node by calling BaseNodeForm's __init__.
        
        This ensures the form builder is properly initialized. The properties
        from BaseNodeProperty must be implemented by subclasses.
        """
        
        BaseNodeForm.__init__(self)


    @abstractmethod
    async def main(self):
        pass