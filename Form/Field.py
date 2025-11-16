from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional
from enum import Enum


class FieldType(str, Enum):
    """
    Enumeration of valid field types.
    Inherits from str to allow direct string comparison and serialization.
    """
    TEXT = "text"
    EMAIL = "email"
    NUMBER = "number"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DATE = "date"
    FILE = "file"
    DERIVED = "derived"


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
    dependsOn: Optional[List['Field']] = None
    options: Optional[List[Dict[str, str]]] = None
    defaultValue: Optional[Any] = None

    def depends_on(self, field: 'Field') -> None:
        """
        Add a field dependency.
        Prevents circular dependencies and duplicates.
        
        Args:
            field: The Field object this field depends on
            
        Raises:
            ValueError: If circular dependency detected or field already in dependsOn
        """
        # Initialize dependsOn if None
        if self.dependsOn is None:
            self.dependsOn = []

        # Check for circular dependency: if field depends on self, it's circular
        if field.dependsOn and self in field.dependsOn:
            raise ValueError(
                f"Circular dependency detected: '{self.name}' depends on '{field.name}', "
                f"but '{field.name}' already depends on '{self.name}'"
            )

        # Check if field already in dependsOn list
        if field in self.dependsOn:
            raise ValueError(f"Field '{field.name}' already in dependsOn list for '{self.name}'")

        # Add field to dependencies
        self.dependsOn.append(field)