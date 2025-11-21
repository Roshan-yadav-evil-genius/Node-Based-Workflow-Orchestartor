from dataclasses import dataclass, field
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
    dependency: Optional[List['Field']] = field(default=None,repr=False) # A dependency is something you rely on to function.
    dependents: Optional[List['Field']] = field(default=None, init=False, repr=False) # A dependent is something that relies on you to function.
    options: Optional[List[Dict[str, str]]] = None
    defaultValue: Optional[Any] = None
    callback: Optional[Callable[[Dict],Dict]] = None

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
        """
        Convert the Field instance to a dictionary representation.
        
        Serializes the field to a dictionary format suitable for JSON
        serialization. Dependencies and dependents are represented as
        lists of field names to avoid circular references.
        
        Returns:
            Dict[str, Any]: A dictionary containing all field properties:
                - type: The field type value
                - name: The field name
                - label: The field label
                - required: Whether the field is required
                - placeholder: The placeholder text
                - options: List of option dictionaries (if applicable)
                - defaultValue: The default value (if any)
                - dependencies: List of dependency field names
                - dependents: List of dependent field names
        """
        return {
            "type": self.type.value,
            "name": self.name,
            "label": self.label,
            "required": self.required,
            "placeholder": self.placeholder,
            "options": self.options,
            "defaultValue": self.defaultValue,
            # Only names returned — NO CYCLES
            "dependencies": [f.name for f in self.dependency] if self.dependency else [],
            "dependents": [f.name for f in self.dependents] if self.dependents else [],
        }