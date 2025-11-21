from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional
from .FieldType import FieldType
from typing import Callable


@dataclass
class Field:
    """
    Pure data model for a form field.
    Its ONLY responsibility: hold data.
    """

    type: FieldType
    name: str
    label: str
    required: bool = False
    placeholder: str = ""
    dependency: Optional[List["Field"]] = field(
        default=None, repr=False
    )  # A dependency is something you rely on to function.
    dependents: Optional[List["Field"]] = field(
        default=None, init=False, repr=False
    )  # A dependent is something that relies on you to function.
    options: Optional[List[Dict[str, str]]] = None
    defaultValue: Optional[Any] = None
    callback: Optional[Callable[[Dict], Dict]] = None
    value: Optional[Any] = None

    def __post_init__(self):
        """
        Initialize reverse dependencies when dependency is set in constructor.
        """
        if self.dependency is not None:
            for dep in self.dependency:
                if dep is not None:
                    if dep.dependents is None:
                        dep.dependents = []
                    if self not in dep.dependents:
                        dep.dependents.append(self)

    def to_dict(self) -> Dict[str, Any]:
        exclude_fields = {"dependency", "dependents", "callback"}
        result = {}

        for field_obj in fields(self):
            if field_obj.name not in exclude_fields:
                value: FieldType = getattr(self, field_obj.name)
                # Special handling for type field
                if field_obj.name == "type":
                    result["type"] = value.value
                else:
                    result[field_obj.name] = value

        # Handle relationship fields separately to avoid cycles
        result["dependencies"] = (
            [f.name for f in self.dependency] if self.dependency else []
        )
        result["dependents"] = (
            [f.name for f in self.dependents] if self.dependents else []
        )
        
        return result