from typing import List, Dict, Any
from .Form.Field import Field, FieldType
from .BaseNode import BaseNode

class Node(BaseNode):
    """
    Concrete implementation of BaseNode for country, state, and language selection.
    
    This node creates a form with three fields: country (select), state (select),
    and language (text). The state and language fields depend on the selected
    country and are populated dynamically using callback functions.
    """

    def _init_form(self):
        """
        Initialize the form with country, state, and language fields.
        
        Creates three form fields:
        - country: A select field with predefined country options
        - state: A select field that depends on the country selection
        - language: A text field that depends on the country selection
        
        Returns:
            SchemaBuilder: The form builder instance with all fields added.
        """
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
        self._form.add(country_field)

        state_field = Field(
            type=FieldType.SELECT,
            name="state",
            label="State",
            required=True,
            placeholder="Select your state",
            dependency=[country_field],
            callback=self.populate_state_of_country,
        )
        self._form.add(state_field)

        language = Field(
            type=FieldType.TEXT,
            name="language",
            label="Language",
            required=True,
            placeholder="Active Language",
            dependency=[country_field],
            callback=self.populate_language_of_country
        )
        self._form.add(language)

        return self._form

    def populate_state_of_country(self, data: Dict) -> Dict:
        """
        Populate state options based on the selected country.
        
        Args:
            data: A dictionary containing form data, expected to have a
                'country' key with the selected country name.
        
        Returns:
            List[str]: A list of state names for the selected country.
                Returns an empty list if the country is not recognized.
        """
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
        """
        Populate language value based on the selected country.
        
        Args:
            data: A dictionary containing form data, expected to have a
                'country' key with the selected country name.
        
        Returns:
            str: The language associated with the selected country.
                Returns an empty string if the country is not recognized.
        """
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
