from typing import Dict, Any
from django import forms
from .Node.Form.BaseForm import BaseForm
from .Node.Node import Node


class PlaceNode(Node):
    """
    Concrete implementation using Django forms with dependencies.
    
    This node creates a form with three fields: country (select), state (select),
    and language (text). The state and language fields depend on the selected
    country and are populated dynamically using callback functions.
    """
    
    class Form(BaseForm):
        country = forms.ChoiceField(
            label="Country",
            required=True,
            choices=[
                ("India", "India"),
                ("United States", "United States"),
                ("Canada", "Canada"),
                ("United Kingdom", "United Kingdom"),
            ],
            initial="India",
            widget=forms.Select(attrs={'placeholder': 'Select your country'})
        )
        
        state = forms.ChoiceField(
            label="State",
            required=True,
            choices=[],  # Will be populated dynamically
            widget=forms.Select(attrs={'placeholder': 'Select your state'})
        )
        
        language = forms.CharField(
            label="Language",
            required=True,
            widget=forms.TextInput(attrs={'placeholder': 'Active Language'})
        )
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Set dependencies and callbacks after field creation
            self.fields['state'].dependency = ["country"]
            self.fields['state'].callback = "populate_state_of_country"
            self.fields['language'].dependency = ["country"]
            self.fields['language'].callback = "populate_language_of_country"
            # Rebuild dependency graph after setting dependencies
            self._build_dependency_graph()
            # Re-resolve callbacks after setting them
            self._resolve_callbacks()

    @property
    def identifier(self) -> str:
        return "place"
    
    @property
    def label(self) -> str:
        return "Place"
    
    @property
    def description(self) -> str:
        return "Node for selecting country, state, and language"
    
    @property
    def icon(self) -> str:
        return "place-icon"

    def _init_form(self):
        """No longer needed with Django forms, but kept for compatibility"""
        return {}

    def populate_state_of_country(self, data: Dict) -> Any:
        """Callback to populate state options based on country."""
        selected_country = data.get("country")
        if selected_country == "India":
            return ["Maharashtra", "Tamil Nadu", "Kerala"]
        elif selected_country == "United States":
            return ["California", "New York", "Texas"]
        elif selected_country == "Canada":
            return ["Ontario", "Quebec", "British Columbia"]
        elif selected_country == "United Kingdom":
            return ["England", "Scotland", "Wales"]
        return []

    def populate_language_of_country(self, data: Dict) -> Any:
        """Callback to populate language based on country."""
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
