from typing import Callable, Dict, Any, List, Optional, Union
from .Field import Field, FieldType
from .Serializer import FieldSerializer

class SchemaBuilder:
    def __init__(self):
        self.fields: List[Field] = []
        self.functions_to_populate_dependent_fields: Dict[str, Callable[[str, Any], Any]] = {} 

    def add(self, field: Field) -> "SchemaBuilder":
        
        if any(f.name == field.name for f in self.fields):
            raise ValueError(f"Duplicate field name: '{field.name}'. Field names must be unique.")
        
        self.fields.append(field)
        
        return self

    def build(self) -> Dict[str, Any]:
        return {
            "fields": [FieldSerializer.to_dict(f) for f in self.fields]
        }

    
    def register_func_to_populate_dependent_fields(self, field: Field, callback: Callable[[str, Any], Any]) -> Dict[str, Any]:
        if field.name in self.functions_to_populate_dependent_fields:
            return self.functions_to_populate_dependent_fields[field.name].append(callback)
        self.functions_to_populate_dependent_fields[field.name] = [callback]
        return self
    
    def get_dependent_fields(self, field_name: str, values: Any) -> List[Field]:
        results={}
        for updated_values in self.functions_to_populate_dependent_fields[field_name]:
            result = updated_values(field_name, values)
            results.update(result)
        return self.results