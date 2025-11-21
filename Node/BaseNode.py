from typing import Dict, Any
from .Form.SchemaBuilder import SchemaBuilder
from abc import ABC,abstractmethod


class BaseNode(ABC):
    def __init__(self):
        self._form = SchemaBuilder()
        
        self._init_form()
    
    @abstractmethod
    def _init_form(self)->Dict:
        raise NotImplementedError

    def form_schema(self) -> Dict[str, Any]:
        return self._form.build()

    def get_populated_field_value(self, data: Dict) -> Dict:
        return self._form.get_populated_field_value(data)
