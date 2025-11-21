from typing import Callable, Dict, Any, List, Optional, Union
from .Field import Field, FieldType
from .Serializer import FieldSerializer

class SchemaBuilder:
    """
    Builder class for constructing form schemas.
    
    This class provides a fluent interface for building form schemas by
    adding fields one at a time. It maintains a list of fields and ensures
    field name uniqueness. Fields can have dependencies on other fields,
    and the builder can compute values for dependent fields based on
    provided data.
    """
    def __init__(self):
        """
        Initialize a new SchemaBuilder instance.
        
        Creates an empty list of fields that will be populated using
        the add method.
        """
        self.fields: List[Field] = []

    def add(self, field: Field) -> "SchemaBuilder":
        """
        Add a field to the schema builder.
        
        Adds a field to the schema and ensures field name uniqueness.
        This method supports method chaining by returning self.
        
        Args:
            field: The Field instance to add to the schema.
        
        Returns:
            SchemaBuilder: Returns self to support method chaining.
        
        Raises:
            ValueError: If a field with the same name already exists
                in the schema.
        """
        if any(f.name == field.name for f in self.fields):
            raise ValueError(f"Duplicate field name: '{field.name}'. Field names must be unique.")
        
        self.fields.append(field)
        
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build and return the complete form schema.
        
        Serializes all added fields into a dictionary format suitable
        for JSON serialization. The resulting dictionary contains a
        'fields' key with a list of serialized field dictionaries.
        
        Returns:
            Dict[str, Any]: A dictionary containing the form schema with
                a 'fields' key mapping to a list of field dictionaries.
        """
        return {
            "fields": [FieldSerializer.to_dict(f) for f in self.fields]
        }
    
    def get_instance_by_name(self, name: str) -> Optional[Field]:
        """
        Retrieve a Field instance from the schema by its name.
        Returns None if not found.
        """
        for field in self.fields:
            if field.name == name:
                return field
        return None
    
    def get_populated_field_value(self, data: Dict) -> Dict:
        """
        Calculate values for dependent fields based on the provided data.
        Returns a dictionary of dependent field names and their computed values.
        """
        result = {}
        for field_name, _ in data.items():
            field_instance = self.get_instance_by_name(field_name)
            if field_instance:  # Safety check in case field not found
                for dependent_field in field_instance.dependents:
                    result[dependent_field.name] = dependent_field.callback(data)
        return result
    
    def populate_values(self, filled_form: Dict) -> None:
        """
        Populate the form fields with values from the provided filled_form dictionary.

        Args:
            filled_form (Dict): A dictionary mapping field names to values.

        This will assign 'value' on each Field object if the name matches.
        """
        for field_name, field_value in filled_form.items():
            field_instance = self.get_instance_by_name(field_name)
            if field_instance is not None:
                field_instance.value = field_value
