from django import forms
from typing import Dict, Any, List, Optional, Callable


class BaseForm(forms.Form):
    """
    Django Form with dependency and dependents tracking.
    Extends Django's forms.Form with additional functionality for handling
    field dependencies and callbacks.
    """
    
    def __init__(self, *args, **kwargs):
        # Extract node_instance if provided (for callback resolution)
        self._node_instance = kwargs.pop('node_instance', None)
        
        # Initialize Django form
        super().__init__(*args, **kwargs)
        
        # Build dependency graph after fields are initialized
        self._build_dependency_graph()
        
        # Resolve callbacks (convert string method names to actual methods)
        self._resolve_callbacks()
    
    def _build_dependency_graph(self):
        """
        Build the dependency graph by analyzing field dependencies.
        For each field with dependencies, update the dependents list of those dependencies.
        """
        for field_name, field in self.fields.items():
            # Check if field has dependency attribute
            if hasattr(field, 'dependency') and field.dependency:
                deps = field.dependency
                if isinstance(deps, list):
                    # Update dependents for each dependency
                    for dep_name in deps:
                        if dep_name in self.fields:
                            dep_field = self.fields[dep_name]
                            # Initialize dependents list if not exists
                            if not hasattr(dep_field, 'dependents'):
                                dep_field.dependents = []
                            # Add current field to dependents if not already present
                            if field_name not in dep_field.dependents:
                                dep_field.dependents.append(field_name)
    
    def _resolve_callbacks(self):
        """
        Resolve callback strings to actual methods.
        If a callback is a string, look it up on the node_instance.
        """
        if not self._node_instance:
            return
        
        for field_name, field in self.fields.items():
            if hasattr(field, 'callback'):
                callback = field.callback
                # If callback is a string, resolve it to a method
                if isinstance(callback, str):
                    method = getattr(self._node_instance, callback, None)
                    if method and callable(method):
                        field.callback = method
    
    def get_populated_field_value(self, data: Dict) -> Dict:
        """
        Calculate values for dependent fields based on provided data.
        
        This method processes the input data and computes values for fields
        that depend on other fields using their callback functions.
        
        Args:
            data: A dictionary containing field names as keys and their
                current values as values.
        
        Returns:
            Dict: A dictionary mapping dependent field names to their
                computed values based on the provided data.
        """
        result = {}
        
        for field_name, field_value in data.items():
            if field_name in self.fields:
                field = self.fields[field_name]
                
                # Check if this field has dependents
                if hasattr(field, 'dependents') and field.dependents:
                    for dependent_name in field.dependents:
                        if dependent_name in self.fields:
                            dependent_field = self.fields[dependent_name]
                            
                            # Execute callback if available
                            if hasattr(dependent_field, 'callback') and dependent_field.callback:
                                try:
                                    if callable(dependent_field.callback):
                                        computed_value = dependent_field.callback(data)
                                        result[dependent_name] = computed_value
                                except Exception as e:
                                    # Handle callback errors gracefully
                                    print(f"Error in callback for {dependent_name}: {e}")
        
        return result
    
    def populate_values(self, filled_form: Dict) -> None:
        """
        Populate form fields with values from the provided filled_form dictionary.
        
        This method assigns values to the corresponding fields in the form
        based on the field names in the provided dictionary.
        
        Args:
            filled_form: A dictionary mapping field names to values that should
                be assigned to the corresponding fields in the form.
        """
        # Initialize form's initial data if not exists
        if not hasattr(self, 'initial') or self.initial is None:
            self.initial = {}
        
        # Populate initial data
        for field_name, field_value in filled_form.items():
            if field_name in self.fields:
                self.initial[field_name] = field_value
        
        # If form is bound, also update cleaned_data
        if self.is_bound:
            if not hasattr(self, '_cleaned_data'):
                self._cleaned_data = {}
            for field_name, field_value in filled_form.items():
                if field_name in self.fields:
                    self._cleaned_data[field_name] = field_value
    
    def form_schema(self) -> Dict[str, Any]:
        """
        Get the complete form schema as a dictionary.
        
        Returns:
            Dict[str, Any]: A dictionary containing the form schema with
                all fields and their configurations. The dictionary has a
                'fields' key containing a list of field dictionaries.
        """
        from .FormSchemaSerializer import FormSchemaSerializer
        return FormSchemaSerializer.to_dict(self)

