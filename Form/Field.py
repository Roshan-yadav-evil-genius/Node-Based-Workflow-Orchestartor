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
    dependsOn: Optional[List[str]] = None
    options: Optional[List[Dict[str, str]]] = None
    default_value: Optional[Any] = None
