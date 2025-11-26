from .Core.BaseForm import BaseForm
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


class TestingForm(BaseForm):
    # subject = forms.CharField(max_length=100)
    COUNTRY_DATA=[
        ("india","India"),
        ("usa","USA")
    ]
    # Base fields with empty choices — we will fill these in __init__
    country = forms.ChoiceField(choices=COUNTRY_DATA)
    state = forms.ChoiceField(choices=[])
    language = forms.ChoiceField(choices=[])
    
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
            return STATE_DATA.get(parent_value, [])
        elif field_name == 'language':
            # Language depends on state
            return LANGUAGE_DATA.get(parent_value, [])
        return []