import django
from django.conf import settings
from django import forms
from django.forms.forms import DeclarativeFieldsMetaclass
from abc import ABCMeta
from DependencyInjector import DependencyInjector

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


# Create a custom metaclass that combines Django's form metaclass with ABCMeta
class FormABCMeta(DeclarativeFieldsMetaclass, ABCMeta):
    """Metaclass that combines Django's form metaclass with ABCMeta."""
    pass


class BaseForm(DependencyInjector, forms.Form, metaclass=FormABCMeta):
    """
    Base form class that provides cascading field dependency functionality.
    All forms with dependent fields should inherit from this class.
    
    This class combines Django's Form with DependencyInjector mixin.
    Child forms MUST implement:
    1. get_field_dependencies() - Returns mapping of parent fields to dependent fields
    2. populate_field(field_name, parent_value) - Returns choices for dependent field
    """
    
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
        This method automatically handles cascading dependencies.
        """
        dependencies = self.get_field_dependencies()
        processed_fields = set()
        
        def process_field(field_name):
            """Recursively process field and its dependencies."""
            if field_name in processed_fields:
                return
            
            field_value = self.get_field_value(field_name)
            if field_value:
                # Update dependent fields
                self._update_dependent_field(field_name, field_value, dependencies)
            
            processed_fields.add(field_name)
            
            # Process dependent fields recursively
            if field_name in dependencies:
                for dependent_field in dependencies[field_name]:
                    process_field(dependent_field)
        
        # Start processing from all parent fields (fields that have dependencies)
        for parent_field in dependencies.keys():
            process_field(parent_field)
    
    def _update_dependent_field(self, parent_field, parent_value, dependencies=None):
        """
        Update a dependent field based on parent field value.
        Calls populate_field() which should be implemented by child classes.
        """
        if dependencies is None:
            dependencies = self.get_field_dependencies()
        
        if parent_field in dependencies:
            for dependent_field in dependencies[parent_field]:
                choices = self.populate_field(dependent_field, parent_value)
                if dependent_field in self.fields:
                    self.fields[dependent_field].choices = choices
    
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
    
    def _clear_dependent_fields(self, parent_field, dependencies=None):
        """
        Clear child fields when parent changes.
        Recursively clears all dependent fields in the dependency chain.
        
        Args:
            parent_field: Name of the parent field that changed
            dependencies: Optional dependencies dict (if None, calls get_field_dependencies())
        """
        if dependencies is None:
            dependencies = self.get_field_dependencies()
        
        if parent_field in dependencies:
            for dependent_field in dependencies[parent_field]:
                # Clear the dependent field value
                self._incremental_data.pop(dependent_field, None)
                # Reset choices
                if dependent_field in self.fields:
                    self.fields[dependent_field].choices = []
                # Recursively clear fields that depend on this dependent field
                self._clear_dependent_fields(dependent_field, dependencies)
    
    def _handle_field_dependencies(self, field_name, value):
        """
        Handle cascading updates when parent fields change.
        Single responsibility: Determine and trigger dependent field updates.
        
        Args:
            field_name: Name of the field that was updated
            value: New value of the field
        """
        dependencies = self.get_field_dependencies()
        
        if field_name in dependencies:
            # Clear dependent fields first
            self._clear_dependent_fields(field_name, dependencies)
            # Update dependent fields
            self._update_dependent_field(field_name, value, dependencies)
    
    def _is_value_changed(self, field_name, new_value):
        """
        Check if the new value differs from current value.
        Single responsibility: Compare new value with current field value.
        
        Args:
            field_name: Name of the field to check
            new_value: The new value to compare
            
        Returns:
            bool: True if value changed, False if same
        """
        # Get current value (before updating)
        current_value = self.get_field_value(field_name)
        
        # Handle None vs empty string comparisons
        # Normalize None and empty string to None for comparison
        normalized_current = None if (current_value is None or current_value == '') else current_value
        normalized_new = None if (new_value is None or new_value == '') else new_value
        
        # Compare normalized values
        return normalized_current != normalized_new
    
    def update_field(self, field_name, value):
        """
        Public interface for updating fields incrementally.
        Automatically handles dependent field updates.
        Single responsibility: Orchestrate the update process by calling specialized methods.
        
        Args:
            field_name: Name of the field to update
            value: Value to set for the field
        """
        # Check if value actually changed
        value_changed = self._is_value_changed(field_name, value)
        
        # Store the value (always update for consistency)
        self._update_incremental_data(field_name, value)
        # Rebind form with updated data (always rebind for consistency)
        self._rebind_form()
        
        # Only handle dependent fields and validate if value actually changed
        if value_changed:
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
