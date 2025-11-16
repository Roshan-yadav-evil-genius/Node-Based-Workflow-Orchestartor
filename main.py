from Form.Field import Field, FieldType
from Form.SchemaBuilder import SchemaBuilder
from Form.Serializer import FieldSerializer
from rich import print


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
        dependsOn=[country_field],
    )
    builder.add(country_field)
    builder.add(state_field)


    print(builder.build())