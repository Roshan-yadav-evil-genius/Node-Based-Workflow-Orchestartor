from typing import Dict, Any
from .Form.SchemaBuilder import SchemaBuilder
from abc import ABC,abstractmethod


class BaseNode(ABC):
    def __init__(self):
        self._schema_builder = SchemaBuilder()
        self._schema()
    
    @abstractmethod
    def _schema(self)->Dict:
        pass

    def schema(self) -> Dict[str, Any]:
        return self._schema_builder.build()

    def get_populated_field_value(self, data: Dict) -> Dict:
        result={}
        for field_name,_ in data.items():
            field_instance = self._schema_builder.get_instance_by_name(field_name)
            for dependent_field in field_instance.dependents:
                result[dependent_field.name]=dependent_field.callback(data)
        return result
