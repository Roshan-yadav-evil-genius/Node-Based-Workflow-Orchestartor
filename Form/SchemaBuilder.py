from typing import Dict, Any, List, Optional, Union
from .Field import Field, FieldType
from .Serializer import FieldSerializer

class SchemaBuilder:
    """
    Builder class to create node schemas with dependency support.
    This integrates with your existing BaseNode.schema() method.
    """
    
    def __init__(self):
        self.fields: List[Field] = []
    
    def add_text(self, name: str, label: str, required: bool = False, 
                 placeholder: str = "", depends_on: Optional[List[str]] = None,
                 default_value: Optional[str] = None) -> 'SchemaBuilder':
        """Add a text input field"""
        self.fields.append(Field(
            type=FieldType.TEXT,
            name=name,
            label=label,
            required=required,
            placeholder=placeholder,
            dependsOn=depends_on,
            default_value=default_value
        ))
        return self
    
    def add_email(self, name: str, label: str, required: bool = False,
                  placeholder: str = "", depends_on: Optional[List[str]] = None) -> 'SchemaBuilder':
        """Add an email input field"""
        self.fields.append(Field(
            type=FieldType.EMAIL,
            name=name,
            label=label,
            required=required,
            placeholder=placeholder,
            dependsOn=depends_on
        ))
        return self
    
    def add_number(self, name: str, label: str, required: bool = False,
                   placeholder: str = "", depends_on: Optional[List[str]] = None,
                   default_value: Optional[Union[int, float]] = None) -> 'SchemaBuilder':
        """Add a number input field"""
        self.fields.append(Field(
            type=FieldType.NUMBER,
            name=name,
            label=label,
            required=required,
            placeholder=placeholder,
            dependsOn=depends_on,
            default_value=default_value
        ))
        return self
    
    def add_textarea(self, name: str, label: str, required: bool = False,
                     placeholder: str = "", depends_on: Optional[List[str]] = None) -> 'SchemaBuilder':
        """Add a textarea field"""
        self.fields.append(Field(
            type=FieldType.TEXTAREA,
            name=name,
            label=label,
            required=required,
            placeholder=placeholder,
            dependsOn=depends_on
        ))
        return self
    
    def add_select(self, name: str, label: str, 
                   options: Optional[List[Dict[str, str]]] = None,
                   required: bool = False, placeholder: str = "",
                   depends_on: Optional[List[str]] = None) -> 'SchemaBuilder':
        """
        Add a select dropdown field.
        
        Args:
            name: Field name
            label: Display label
            options: List of dicts with 'value' and 'label' keys (optional if depends_on is set)
            required: Whether field is required
            placeholder: Placeholder text
            depends_on: List of field names this field depends on
        """
        self.fields.append(Field(
            type=FieldType.SELECT,
            name=name,
            label=label,
            required=required,
            placeholder=placeholder,
            dependsOn=depends_on,
            options=options
        ))
        return self
    
    def add_checkbox(self, name: str, label: str, required: bool = False,
                     depends_on: Optional[List[str]] = None) -> 'SchemaBuilder':
        """Add a checkbox field"""
        self.fields.append(Field(
            type=FieldType.CHECKBOX,
            name=name,
            label=label,
            required=required,
            dependsOn=depends_on
        ))
        return self
    
    def add_radio(self, name: str, label: str, choices: List[Dict[str, str]],
                  required: bool = False, depends_on: Optional[List[str]] = None) -> 'SchemaBuilder':
        """Add a radio button group"""
        self.fields.append(Field(
            type=FieldType.RADIO,
            name=name,
            label=label,
            required=required,
            dependsOn=depends_on,
            options=choices
        ))
        return self
    
    def add_date(self, name: str, label: str, required: bool = False,
                 depends_on: Optional[List[str]] = None) -> 'SchemaBuilder':
        """Add a date picker field"""
        self.fields.append(Field(
            type=FieldType.DATE,
            name=name,
            label=label,
            required=required,
            dependsOn=depends_on
        ))
        return self
    
    def add_file(self, name: str, label: str, required: bool = False,
                 depends_on: Optional[List[str]] = None) -> 'SchemaBuilder':
        """Add a file upload field"""
        self.fields.append(Field(
            type=FieldType.FILE,
            name=name,
            label=label,
            required=required,
            dependsOn=depends_on
        ))
        return self
    
    def add_derived(self, name: str, label: str,
                    depends_on: List[str], required: bool = False) -> 'SchemaBuilder':
        """
        Add a derived field that depends on other fields.
        The value is computed via get_dependent_options().
        
        Args:
            name: Field name
            label: Display label
            depends_on: List of field names this field depends on (required for derived)
            required: Whether field is required
        """
        if not depends_on:
            raise ValueError("Derived fields must have at least one dependency")
        
        self.fields.append(Field(
            type=FieldType.DERIVED,
            name=name,
            label=label,
            required=required,
            dependsOn=depends_on
        ))
        return self
    
    def add_custom(self, field: Field) -> 'SchemaBuilder':
        """Add a custom field definition"""
        self.fields.append(field)
        return self
    
    def build(self) -> Dict[str, Any]:
        """
        Build the final schema dictionary matching your existing format.
        Returns: {"fields": [...]}
        """
        return {
            "fields": [FieldSerializer.to_dict(field) for field in self.fields]
        }
    
    def get_field_names(self) -> List[str]:
        """Get list of all field names in the schema"""
        return [field.name for field in self.fields]
    
    def get_dependent_fields(self, field_name: str) -> List[str]:
        """Get list of fields that depend on the given field"""
        dependent = []
        for field in self.fields:
            if field.dependsOn and field_name in field.dependsOn:
                dependent.append(field.name)
        return dependent