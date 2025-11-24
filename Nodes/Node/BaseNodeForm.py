from typing import Dict, Any
from abc import ABC, abstractmethod
from .Form.BaseForm import BaseForm


class BaseNodeForm(ABC):
    """
    Abstract base class for form schema management using Django forms.
    
    This class provides functionality for building and managing form schemas
    using Django forms. Subclasses should define a nested Form class that
    inherits from BaseForm with fields as class attributes.
    """
    
    def __init__(self):
        """
        Initialize the BaseNodeForm with a Django Form instance.
        
        Detects the nested Form class in the subclass and instantiates it
        with a reference to this node instance for callback resolution.
        """
        # Get the Form class from the subclass
        form_class = self._get_form_class()
        if form_class is None:
            raise ValueError(
                f"{self.__class__.__name__} must define a nested Form class "
                "that inherits from BaseForm"
            )
        
        # Instantiate the form with reference to this node
        self._form = form_class(node_instance=self)
    
    def _get_form_class(self):
        """
        Get the nested Form class from the subclass.
        
        Returns:
            type: The Form class if found, None otherwise
        """
        # Look for a nested Form class
        for attr_name in dir(self.__class__):
            attr = getattr(self.__class__, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, BaseForm) and 
                attr is not BaseForm):
                return attr
        return None
    
    def _init_form(self) -> Dict:
        """
        DEPRECATED: No longer needed with Django forms.
        
        Kept for backward compatibility. Subclasses can override this
        to return an empty dict or implement custom logic if needed.
        
        Returns:
            Dict: Empty dictionary (or custom implementation)
        """
        return {}

    def form_schema(self) -> Dict[str, Any]:
        """
        Get the complete form schema as a dictionary.
        
        Returns:
            Dict[str, Any]: A dictionary containing the form schema with
                all fields and their configurations. The dictionary has a
                'fields' key containing a list of field dictionaries.
        """
        return self._form.form_schema()

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
    
    def populate_values(self, filled_form: Dict) -> None:
        """
        Populate the form fields with values from the provided filled_form dictionary.
        
        This method assigns values to the corresponding fields in the form
        based on the field names in the provided dictionary.
        
        Args:
            filled_form: A dictionary mapping field names to values that should
                be assigned to the corresponding fields in the form.
        """
        self._form.populate_values(filled_form)