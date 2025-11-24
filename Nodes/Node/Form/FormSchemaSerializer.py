from typing import Dict, Any, List
from django import forms


class FormSchemaSerializer:
    """
    Serializes Django forms to API schema format.
    Converts Django form fields to the API-compatible dictionary format.
    """
    
    # Map Django field types to API field types
    FIELD_TYPE_MAP = {
        forms.CharField: "text",
        forms.EmailField: "email",
        forms.IntegerField: "number",
        forms.FloatField: "number",
        forms.DecimalField: "number",
        forms.Textarea: "textarea",
        forms.ChoiceField: "select",
        forms.ModelChoiceField: "select",
        forms.CheckboxInput: "checkbox",
        forms.RadioSelect: "radio",
        forms.DateField: "date",
        forms.FileField: "file",
    }
    
    @staticmethod
    def _get_field_type(field: forms.Field) -> str:
        """
        Get API field type from Django field.
        
        Args:
            field: Django form field instance
            
        Returns:
            str: API field type string
        """
        field_class = field.__class__
        
        # Check direct mapping
        if field_class in FormSchemaSerializer.FIELD_TYPE_MAP:
            return FormSchemaSerializer.FIELD_TYPE_MAP[field_class]
        
        # Check widget type for some fields
        widget_class = field.widget.__class__
        if widget_class == forms.Textarea:
            return "textarea"
        elif widget_class == forms.CheckboxInput:
            return "checkbox"
        elif widget_class == forms.RadioSelect:
            return "radio"
        
        # Default to text
        return "text"
    
    @staticmethod
    def _get_field_options(field: forms.Field) -> List[Dict[str, str]]:
        """
        Extract options from ChoiceField.
        
        Args:
            field: Django form field instance
            
        Returns:
            List[Dict[str, str]]: List of option dictionaries with label and value
        """
        if isinstance(field, (forms.ChoiceField, forms.ModelChoiceField)):
            options = []
            for choice_value, choice_label in field.choices:
                if choice_value:  # Skip empty choices
                    options.append({
                        "label": str(choice_label),
                        "value": str(choice_value)
                    })
            return options
        return []
    
    @staticmethod
    def to_dict(form: forms.Form) -> Dict[str, Any]:
        """
        Convert Django form to API schema dictionary.
        
        Args:
            form: Django form instance
            
        Returns:
            Dict[str, Any]: API schema dictionary with 'fields' key
        """
        fields = []
        
        for field_name, field in form.fields.items():
            field_dict = {
                "name": field_name,
                "type": FormSchemaSerializer._get_field_type(field),
                "label": field.label or field_name,
                "required": field.required,
            }
            
            # Add placeholder if available in widget attrs
            if hasattr(field.widget, 'attrs') and 'placeholder' in field.widget.attrs:
                field_dict["placeholder"] = field.widget.attrs['placeholder']
            
            # Add default value
            # Check field's initial value first
            if hasattr(field, 'initial') and field.initial is not None:
                field_dict["defaultValue"] = field.initial
            # Then check form's initial data
            elif hasattr(form, 'initial') and field_name in form.initial:
                field_dict["defaultValue"] = form.initial[field_name]
            
            # Add options for choice fields
            options = FormSchemaSerializer._get_field_options(field)
            if options:
                field_dict["options"] = options
            
            # Add dependencies if field has dependency attribute
            if hasattr(field, 'dependency') and field.dependency:
                field_dict["dependencies"] = field.dependency
            
            # Add dependents if field has dependents attribute
            if hasattr(field, 'dependents') and field.dependents:
                field_dict["dependents"] = field.dependents
            
            # Add value if form is bound and has cleaned_data
            if form.is_bound and hasattr(form, 'cleaned_data') and field_name in form.cleaned_data:
                field_dict["value"] = form.cleaned_data[field_name]
            # Also check if field has a value attribute
            elif hasattr(field, 'value'):
                field_dict["value"] = field.value
            
            # Remove None/empty optional fields (matching original behavior)
            result = {}
            for k, v in field_dict.items():
                # Include required fields always
                if k in ("name", "type", "label", "required"):
                    result[k] = v
                # Include optional fields only if they have values
                elif v not in (None, "", []):
                    result[k] = v
            
            fields.append(result)
        
        return {"fields": fields}

