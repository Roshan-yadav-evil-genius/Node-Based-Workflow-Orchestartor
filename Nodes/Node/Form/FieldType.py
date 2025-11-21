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