from Form.Field import Field, FieldType
from Form.Serializer import FieldSerializer
from dataclasses import asdict
import json

# Create a test field
field = Field(
    type=FieldType.TEXT,
    name="test_field",
    label="Test Field",
    required=True,
    placeholder="Enter text",
    default_value="default"
)

print("=" * 60)
print("DIRECT asdict() OUTPUT:")
print("=" * 60)
print(json.dumps(asdict(field), indent=2, default=str))

print("\n" + "=" * 60)
print("SERIALIZER OUTPUT:")
print("=" * 60)
print(json.dumps(FieldSerializer.to_dict(field), indent=2, default=str))

print("\n" + "=" * 60)
print("KEY DIFFERENCES:")
print("=" * 60)
print("1. default_value -> defaultValue (snake_case to camelCase)")
print("2. Optional fields only included if they have values")
print("3. Enum explicitly converted to string")

