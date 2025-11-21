from typing import Callable, Dict, Any, List, Optional, Union
from .Field import Field, FieldType
from .Serializer import FieldSerializer
import warnings

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
    
    def get_instance_by_name(self, name: str) -> Optional[Field]:
        """
        Retrieve a Field instance from the schema by its name.
        Returns None if not found.
        """
        for field in self.fields:
            if field.name == name:
                return field
        return None
