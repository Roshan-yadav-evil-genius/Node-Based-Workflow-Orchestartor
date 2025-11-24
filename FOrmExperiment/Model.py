import django
from django.conf import settings
from django import forms

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='dummy-secret-key-for-testing',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
    )
    django.setup()

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

class ContactForm(forms.Form):
    # subject = forms.CharField(max_length=100)
    # message = forms.CharField(widget=forms.Textarea)
    # sender = forms.EmailField()
    # cc_myself = forms.BooleanField(required=False)
    COUNTRY_DATA=[
        ("india","India"),
        ("usa","USA")
    ]
    # Base fields with empty choices — we will fill these in __init__
    country = forms.ChoiceField(choices=COUNTRY_DATA )
    state = forms.ChoiceField(choices=[])
    language = forms.ChoiceField(choices=[])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_dependent_fields()
    
    def _get_field_value(self, field_name):
        """
        Helper method to get field value from data (bound forms) or initial (unbound forms).
        
        Args:
            field_name: Name of the field to retrieve
            
        Returns:
            Field value if found, None otherwise
        """
        if self.is_bound and self.data and field_name in self.data:
            return self.data.get(field_name)
        elif field_name in self.initial:
            return self.initial.get(field_name)
        return None
    
    def _initialize_dependent_fields(self):
        """
        Initialize dependent fields based on parent field values.
        This method handles the cascade of field dependencies:
        - Country -> States
        - State -> Languages
        """
        # Initialize states based on country
        country_value = self._get_field_value('country')
        if country_value:
            self.populate_states(country_value)
        
        # Initialize languages based on state
        state_value = self._get_field_value('state')
        if country_value and state_value:
            self.populate_languages(state_value)
    
    def populate_states(self, country_value):
        """
        Connected function that populates states based on selected country.
        This is called automatically when country field is set.
        """
        if country_value in STATE_DATA:
            self.fields['state'].choices = STATE_DATA[country_value]
        else:
            self.fields['state'].choices = []
    
    def populate_languages(self, state_value):
        """
        Connected function that populates languages based on selected state.
        This is called automatically when state field is set.
        """
        if state_value in LANGUAGE_DATA:
            self.fields['language'].choices = LANGUAGE_DATA[state_value]
        else:
            self.fields['language'].choices = []