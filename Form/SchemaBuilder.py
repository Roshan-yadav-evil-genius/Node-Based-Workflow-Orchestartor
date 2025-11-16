from typing import Dict, Any, List, Optional, Union
from .Field import Field, FieldType
from .Serializer import FieldSerializer

class SchemaBuilder:
    def __init__(self):
        self.fields: List[Field] = []

    def add(self, field: Field) -> "SchemaBuilder":
        
        if any(f.name == field.name for f in self.fields):
            raise ValueError(f"Duplicate field name: '{field.name}'. Field names must be unique.")
        
        self.fields.append(field)
        
        return self

    def build(self) -> Dict[str, Any]:
        return {
            "fields": [FieldSerializer.to_dict(f) for f in self.fields]
        }

    
    def get_dependent_fields(self, field_name: str) -> List[str]:
        """
        Get list of field names that depend on the given field name.
        
        Args:
            field_name: Name of the field to check dependencies for
            
        Returns:
            List of field names that depend on the given field
        """
        dependent = []
        for field in self.fields:
            if field.dependsOn:
                # Check if any Field in dependsOn has the matching name
                if any(dep.name == field_name for dep in field.dependsOn):
                    dependent.append(field.name)
        return dependent