"""
Field Parser Module

This module provides utilities for parsing Django form fields into JSON structures.
Each function follows the Single Responsibility Principle.
"""

from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional


def normalize_attribute_value(attr_value: Any) -> Any:
    """
    Normalize HTML attribute values to appropriate Python types.
    
    Converts:
    - Lists to strings (space-separated) or single values
    - Empty/None values to True (boolean attributes)
    - Numeric strings to int or float
    - Other values remain as-is
    
    Args:
        attr_value: The raw attribute value from HTML parsing
        
    Returns:
        Normalized value (int, float, bool, str, or list)
    """
    if isinstance(attr_value, list):
        if len(attr_value) > 1:
            return ' '.join(attr_value)
        elif len(attr_value) == 1:
            return attr_value[0]
        else:
            return True
    elif attr_value is None or attr_value == '':
        return True
    elif isinstance(attr_value, str):
        if attr_value.isdigit():
            return int(attr_value)
        elif attr_value.replace('.', '', 1).replace('-', '', 1).isdigit():
            return float(attr_value)
    return attr_value


def extract_select_options(select_tag: Any) -> List[Dict[str, Any]]:
    """
    Extract option elements from a select tag.
    
    Args:
        select_tag: BeautifulSoup Tag object representing a select element
        
    Returns:
        List of dictionaries, each containing:
        - 'value': The option's value attribute
        - 'text': The option's display text
        - 'selected': True if the option is selected (optional)
    """
    options = []
    for option in select_tag.find_all('option'):
        option_data = {
            'value': option.get('value', ''),
            'text': option.get_text(strip=True)
        }
        if option.get('selected'):
            option_data['selected'] = True
        options.append(option_data)
    return options


def extract_tag_attributes(tag: Any) -> Dict[str, Any]:
    """
    Extract and normalize all attributes from an HTML tag.
    
    Args:
        tag: BeautifulSoup Tag object
        
    Returns:
        Dictionary of normalized attribute name-value pairs
    """
    attributes = {}
    for attr_name, attr_value in tag.attrs.items():
        attributes[attr_name] = normalize_attribute_value(attr_value)
    return attributes


def parse_field_to_json(field: Any) -> Dict[str, Any]:
    """
    Parse a Django form field into a JSON-serializable dictionary.
    
    Extracts:
    - Tag name (input, select, textarea, etc.)
    - Field label
    - Field errors
    - All HTML attributes (normalized)
    - Current field value
    - Options (for select elements)
    
    Args:
        field: Django form field (BoundField instance)
        
    Returns:
        Dictionary containing parsed field information
    """
    soup = BeautifulSoup(str(field), 'html.parser')
    tag = soup.find()
    
    if not tag:
        return {}
    
    result = {
        'tag': tag.name,
        'label': str(field.label) if field.label else '',
        'errors': list(field.errors) if field.errors else []
    }
    
    # Extract and normalize tag attributes
    attributes = extract_tag_attributes(tag)
    result.update(attributes)
    
    # Extract current field value
    field_value = field.value()
    if field_value is not None:
        result['value'] = field_value
    
    # Handle select elements - extract options
    if tag.name == 'select':
        options = extract_select_options(tag)
        if options:
            result['options'] = options
    
    return result

