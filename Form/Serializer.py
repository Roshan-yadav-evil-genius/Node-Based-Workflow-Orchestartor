from dataclasses import asdict
from typing import Any, Dict
from .Field import Field, FieldType

class FieldSerializer:
    """
    Converts Field dataclass to API schema dict.
    Main purpose: Transform field names (default_value -> defaultValue) for API compatibility.
    """

    @staticmethod
    def to_dict(field_obj: Field) -> Dict[str, Any]:
        """
        Convert Field to API dict format.
        Main transformations:
        - default_value -> defaultValue (snake_case to camelCase)
        - dependsOn: List[Field] -> List[str] (convert Field objects to field names)
        """
        raw = asdict(field_obj)
        
        # Convert enum to string
        if isinstance(raw["type"], FieldType):
            raw["type"] = raw["type"].value
        else:
            raw["type"] = str(raw["type"])
        
        # Convert dependsOn from List[Field] to List[str] (field names)
        if "dependsOn" in raw and raw["dependsOn"] is not None:
            # asdict() recursively converts Field objects to dicts, extract 'name' from each
            raw["dependsOn"] = [dep["name"] for dep in raw["dependsOn"] if isinstance(dep, dict) and "name" in dep]
        
        # Remove None/empty optional fields (matching original behavior)
        result = {}
        for k, v in raw.items():
            # Include required fields always
            if k in ("name", "type", "label", "required"):
                result[k] = v
            # Include optional fields only if they have values
            elif v not in (None, "", []):
                result[k] = v
        
        return result

