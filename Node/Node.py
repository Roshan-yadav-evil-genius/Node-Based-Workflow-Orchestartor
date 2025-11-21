from typing import List, Dict, Any
from .Form.Field import Field, FieldType
from .BaseNode import BaseNode

class Node(BaseNode):

    def _init_node_schema(self):
        country_field = Field(
            type=FieldType.SELECT,
            name="country",
            label="Country",
            required=True,
            placeholder="Select your country",
            defaultValue="India",
            options=[
                {"label": "India", "value": "India"},
                {"label": "United States", "value": "United States"},
                {"label": "Canada", "value": "Canada"},
                {"label": "United Kingdom", "value": "United Kingdom"},
            ],
        )
        self._schema_builder.add(country_field)

        state_field = Field(
            type=FieldType.SELECT,
            name="state",
            label="State",
            required=True,
            placeholder="Select your state",
            dependency=[country_field],
            callback=self.populate_state_of_country,
        )
        self._schema_builder.add(state_field)

        language = Field(
            type=FieldType.TEXT,
            name="language",
            label="Language",
            required=True,
            placeholder="Active Language",
            dependency=[country_field],
            callback=self.populate_language_of_country
        )
        self._schema_builder.add(language)

        return self._schema_builder

    def populate_state_of_country(self, data: Dict) -> Dict:
        selected_country = data.get("country")
        if selected_country == "India":
            return ["Maharashtra", "Tamil Nadu", "Kerala"]
        elif selected_country == "United States":
            return  ["California", "New York", "Texas"]
        elif selected_country == "Canada":
            return ["Ontario", "Quebec", "British Columbia"]
        elif selected_country == "United Kingdom":
            return ["England", "Scotland", "Wales"]
        return []

    def populate_language_of_country(self, data: Dict):
        selected_country = data.get("country")
        if selected_country == "India":
            return "Hindi"
        elif selected_country == "United States":
            return "Spanish"
        elif selected_country == "Canada":
            return "French"
        elif selected_country == "United Kingdom":
            return "Welsh"
        return ""
