from typing import Dict, Any
from .Form.SchemaBuilder import SchemaBuilder
from abc import ABC,abstractmethod


class BaseNode(ABC):
    """
    Abstract base class for nodes that manage form schemas.
    
    This class provides a foundation for creating nodes that can build and manage
    form schemas using a SchemaBuilder. Subclasses must implement the _init_form
    method to define their specific form structure.
    """
    def __init__(self):
        """
        Initialize the BaseNode with a SchemaBuilder instance.
        
        Creates a new SchemaBuilder and calls _init_form to set up the form
        structure defined by the subclass.
        """
        self._form = SchemaBuilder()
        
        self._init_form()
    
    @abstractmethod
    def _init_form(self)->Dict:
        """
        Initialize the form schema for this node.
        
        This abstract method must be implemented by subclasses to define
        the form fields and their configurations. It should add fields to
        self._form using the SchemaBuilder's add method.
        
        Returns:
            Dict: The form schema dictionary (typically returned by
                self._form.build() or self._form itself).
        
        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError

    def form_schema(self) -> Dict[str, Any]:
        """
        Get the complete form schema as a dictionary.
        
        Returns:
            Dict[str, Any]: A dictionary containing the form schema with
                all fields and their configurations. The dictionary has a
                'fields' key containing a list of field dictionaries.
        """
        return self._form.build()

    def get_populated_field_value(self, data: Dict) -> Dict:
        """
        Calculate values for dependent fields based on provided data.
        
        This method processes the input data and computes values for fields
        that depend on other fields using their callback functions.
        
        Args:
            data: A dictionary containing field names as keys and their
                current values as values.
        
        Returns:
            Dict: A dictionary mapping dependent field names to their
                computed values based on the provided data.
        """
        return self._form.get_populated_field_value(data)
