from typing import List
from Form.Field import Field, FieldType
from Form.SchemaBuilder import SchemaBuilder
from Form.Serializer import FieldSerializer
from rich import print
import json

def get_states_for_country(country: str) -> List[str]:
    if country == "India":
        return {"state": ["Maharashtra", "Tamil Nadu", "Kerala"]}
    elif country == "United States":
        return {"state": ["California", "New York", "Texas"]}
    elif country == "Canada":
        return {"state": ["Ontario", "Quebec", "British Columbia"]}
    elif country == "United Kingdom":
        return {"state": ["England", "Scotland", "Wales"]}
    return {}

if __name__ == "__main__":
    builder = SchemaBuilder()
    country_field = Field(
        type=FieldType.SELECT,
        name="country",
        label="Country",
        required=True,
        placeholder="Select your country",
        defaultValue="India",
        options=[
            {
                "label": "India",
                "value": "India"
            },
            {
                "label": "United States",
                "value": "United States"
            },
            {
                "label": "Canada",
                "value": "Canada"
            },
            {
                "label": "United Kingdom",
                "value": "United Kingdom"
            }
        ]
    )
    state_field = Field(
        type=FieldType.SELECT,
        name="state",
        label="State",
        required=True,
        placeholder="Select your state",
        dependency=[country_field],
    )
    builder.add(country_field).add(state_field)

    builder.register_func_to_populate_dependent_fields(country_field, get_states_for_country)
    print(builder.build())

    with open("schema.json", "w") as f:
        json.dump(builder.build(), f, indent=4)

    print(builder.get_dependent_fields("country", "India"))

