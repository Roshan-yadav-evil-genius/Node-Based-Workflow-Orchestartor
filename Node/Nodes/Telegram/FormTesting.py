from ...Core.Form.Core.BaseForm import BaseForm
from django import forms
# State data mapping for countries
STATE_DATA = {
    "india": [
        ("maharashtra", "Maharashtra"),
        ("karnataka", "Karnataka"),
        ("tamil_nadu", "Tamil Nadu"),
        ("gujarat", "Gujarat"),
        ("rajasthan", "Rajasthan"),
    ],
    "usa": [
        ("california", "California"),
        ("texas", "Texas"),
        ("new_york", "New York"),
        ("florida", "Florida"),
        ("illinois", "Illinois"),
    ]
}

# Language data mapping for states
LANGUAGE_DATA = {
    "maharashtra": [
        ("marathi", "Marathi"),
        ("hindi", "Hindi"),
        ("english", "English"),
    ],
    "karnataka": [
        ("kannada", "Kannada"),
        ("hindi", "Hindi"),
        ("english", "English"),
    ],
    "tamil_nadu": [
        ("tamil", "Tamil"),
        ("hindi", "Hindi"),
        ("english", "English"),
    ],
    "gujarat": [
        ("gujarati", "Gujarati"),
        ("hindi", "Hindi"),
        ("english", "English"),
    ],
    "rajasthan": [
        ("rajasthani", "Rajasthani"),
        ("hindi", "Hindi"),
        ("english", "English"),
    ],
    "california": [
        ("english", "English"),
        ("spanish", "Spanish"),
        ("chinese", "Chinese"),
    ],
    "texas": [
        ("english", "English"),
        ("spanish", "Spanish"),
    ],
    "new_york": [
        ("english", "English"),
        ("spanish", "Spanish"),
        ("chinese", "Chinese"),
    ],
    "florida": [
        ("english", "English"),
        ("spanish", "Spanish"),
    ],
    "illinois": [
        ("english", "English"),
        ("spanish", "Spanish"),
        ("polish", "Polish"),
    ],
}


class FormTesting(BaseForm):
    # subject = forms.CharField(max_length=100)
    COUNTRY_DATA=[
        ("", "-- Select Country --"),
        ("india", "India"),
        ("usa", "USA")
    ]
    # Base fields with empty choices — we will fill these in __init__
    country = forms.ChoiceField(choices=COUNTRY_DATA, required=False)
    state = forms.ChoiceField(choices=[("", "-- Select State --")], required=False)
    language = forms.ChoiceField(choices=[("", "-- Select Language --")], required=False)
    
    def get_field_dependencies(self):
        """
        REQUIRED: Define which fields depend on which parent fields.
        """
        return {
            'country': ['state'],      # When country changes, update state
            'state': ['language']      # When state changes, update language
        }
    
    def populate_field(self, field_name, parent_value):
        """
        REQUIRED: Provide choices for dependent fields based on parent value.
        """
        if field_name == 'state':
            # State depends on country
            choices = STATE_DATA.get(parent_value, [])
            return [("", "-- Select State --")] + list(choices)
        elif field_name == 'language':
            # Language depends on state
            choices = LANGUAGE_DATA.get(parent_value, [])
            return [("", "-- Select Language --")] + list(choices)
        return []