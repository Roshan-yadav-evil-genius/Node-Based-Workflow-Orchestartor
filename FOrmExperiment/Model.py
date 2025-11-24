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
        self._incremental_data = {}
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
        country_value = self.get_field_value('country')
        if country_value:
            self.populate_states(country_value)
        
        # Initialize languages based on state
        state_value = self.get_field_value('state')
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
    
    def _update_incremental_data(self, field_name, value):
        """
        Manage incremental data storage.
        Single responsibility: Store field values for incremental updates.
        
        Args:
            field_name: Name of the field to update
            value: Value to store for the field
        """
        self._incremental_data[field_name] = value
    
    def _rebind_form(self):
        """
        Rebind form with updated data.
        Single responsibility: Merge incremental data with existing form data and rebind.
        """
        # Merge incremental data with existing data
        updated_data = {}
        if self.is_bound and self.data:
            # Convert QueryDict to dict if needed
            if hasattr(self.data, 'dict'):
                updated_data.update(self.data.dict())
            else:
                updated_data.update(dict(self.data))
        updated_data.update(self._incremental_data)
        
        # Rebind the form with updated data
        self.data = updated_data
        self.is_bound = True
    
    def _clear_dependent_fields(self, parent_field):
        """
        Clear child fields when parent changes.
        Single responsibility: Remove values and reset choices for dependent fields.
        
        Args:
            parent_field: Name of the parent field that changed
        """
        if parent_field == 'country':
            # Clear state and language when country changes
            self._incremental_data.pop('state', None)
            self._incremental_data.pop('language', None)
            self.fields['state'].choices = []
            self.fields['language'].choices = []
        elif parent_field == 'state':
            # Clear language when state changes
            self._incremental_data.pop('language', None)
            self.fields['language'].choices = []
    
    def _handle_field_dependencies(self, field_name, value):
        """
        Handle cascading updates when parent fields change.
        Single responsibility: Determine and trigger dependent field updates.
        
        Args:
            field_name: Name of the field that was updated
            value: New value of the field
        """
        if field_name == 'country':
            # Clear dependent fields first
            self._clear_dependent_fields('country')
            # Populate states based on country
            self.populate_states(value)
        elif field_name == 'state':
            # Clear dependent fields first
            self._clear_dependent_fields('state')
            # Populate languages based on state
            self.populate_languages(value)
    
    def update_field(self, field_name, value):
        """
        Public interface for updating fields incrementally.
        Single responsibility: Orchestrate the update process by calling specialized methods.
        
        Args:
            field_name: Name of the field to update
            value: Value to set for the field
        """
        # Store the value
        self._update_incremental_data(field_name, value)
        # Rebind form with updated data
        self._rebind_form()
        # Handle dependent field updates
        self._handle_field_dependencies(field_name, value)
        # Validate the updated field
        self._validate_field(field_name)
    
    def get_field_value(self, field_name):
        """
        Get current field value from any source.
        Single responsibility: Retrieve field value, checking incremental data first.
        
        Args:
            field_name: Name of the field to retrieve
            
        Returns:
            Field value if found, None otherwise
        """
        # Check incremental data first (most recent)
        if field_name in self._incremental_data:
            return self._incremental_data[field_name]
        # Fall back to regular field value retrieval
        return self._get_field_value(field_name)
    
    def _validate_field(self, field_name):
        """
        Validate a single field.
        Single responsibility: Validate a specific field and store errors.
        
        Args:
            field_name: Name of the field to validate
            
        Returns:
            bool: True if field is valid, False otherwise
        """
        if field_name not in self.fields:
            return False
        
        # Get the field value
        field_value = self.get_field_value(field_name)
        
        # Clear previous errors for this field
        # Access _errors directly to avoid triggering full validation
        if hasattr(self, '_errors') and self._errors and field_name in self._errors:
            del self._errors[field_name]
        
        # Validate the field
        try:
            # Use Django's field validation
            self.fields[field_name].clean(field_value)
            return True
        except forms.ValidationError as e:
            # Store validation errors
            # Initialize _errors if it doesn't exist
            if not hasattr(self, '_errors') or self._errors is None:
                from django.forms.utils import ErrorDict
                self._errors = ErrorDict()
            # Store the error messages
            self._errors[field_name] = self.error_class(e.messages)
            return False
    
    def validate(self):
        """
        Trigger full form validation.
        Single responsibility: Validate all form fields.
        
        Returns:
            bool: True if form is valid, False otherwise
        """
        self.full_clean()
        return self.is_valid()
    
    def get_errors(self):
        """
        Get all form errors after validation.
        Single responsibility: Retrieve validation errors.
        
        Returns:
            dict: Dictionary of field names to error lists
        """
        return self.errors