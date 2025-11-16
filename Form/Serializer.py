from dataclasses import asdict
from typing import Any, Dict
from .Field import Field

class FieldSerializer:
    """
    Responsible ONLY for converting FormField -> API schema dict.
    Zero business logic in the model.
    """

    @staticmethod
    def to_dict(field_obj: Field) -> Dict[str, Any]:
        raw = asdict(field_obj)

        # Transform python naming -> API-facing format
        # FieldType inherits from str, so it serializes directly to string
        result = {
            "name": raw["name"],
            "type": str(raw["type"]),  # Convert enum to string value
            "label": raw["label"],
            "required": raw["required"],
        }

        FieldSerializer._include_optional(result, raw)

        return result

    @staticmethod
    def _include_optional(result: Dict[str, Any], raw: Dict[str, Any]):
        """Handles all optional keys in one place"""
        if raw.get("placeholder"):
            result["placeholder"] = raw["placeholder"]

        if raw.get("dependsOn"):
            result["dependsOn"] = raw["dependsOn"]

        if raw.get("options"):
            result["options"] = raw["options"]

        if raw.get("default_value") is not None:
            result["defaultValue"] = raw["default_value"]
