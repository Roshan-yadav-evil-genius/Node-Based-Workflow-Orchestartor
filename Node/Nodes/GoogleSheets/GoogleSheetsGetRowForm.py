"""
Google Sheets Get Row Form

Single Responsibility: Form field definitions and cascading dependencies.

This form handles:
- Google account selection (loaded from backend API)
- Spreadsheet selection (cascades from account)
- Sheet selection (cascades from spreadsheet)
- Row number input
- Header row configuration
"""

from django import forms
import requests
import structlog

from ...Core.Form.Core.BaseForm import BaseForm

logger = structlog.get_logger(__name__)


class DynamicChoiceField(forms.ChoiceField):
    """
    ChoiceField that skips choice validation for dynamically populated options.
    
    Use this for fields whose choices are loaded dynamically (e.g., from API)
    and aren't available at form instantiation time during node execution.
    """
    
    def validate(self, value):
        """Skip choice validation - only check if required."""
        if value in self.empty_values and self.required:
            raise forms.ValidationError(
                self.error_messages['required'], 
                code='required'
            )


def get_google_account_choices():
    """
    Fetch available Google accounts from backend API.
    
    Returns:
        List of (id, display_text) tuples for ChoiceField
    """
    try:
        response = requests.get(
            'http://127.0.0.1:7878/api/auth/google/accounts/choices/',
            timeout=5
        )
        if response.status_code == 200:
            accounts = response.json()
            return [("", "-- Select Account --")] + [
                (str(a['id']), f"{a['name']} ({a['email']})") 
                for a in accounts
            ]
    except Exception as e:
        logger.warning("Failed to fetch Google accounts", error=str(e))
    
    return [("", "-- Select Account --")]


class GoogleSheetsGetRowForm(BaseForm):
    """
    Form for Google Sheets Get Row node with cascading dropdowns.
    
    Field Dependencies:
    - google_account -> spreadsheet (selecting account loads spreadsheets)
    - spreadsheet -> sheet (selecting spreadsheet loads sheets)
    
    The form uses the existing BaseForm dependency system to handle
    cascading field updates via the frontend.
    """
    
    google_account = forms.ChoiceField(
        choices=[("", "-- Select Account --")],
        required=True,
        help_text="Select a connected Google account"
    )
    
    # Use DynamicChoiceField for fields populated via cascading API calls
    spreadsheet = DynamicChoiceField(
        choices=[("", "-- Select Spreadsheet --")],
        required=True,
        help_text="Select a Google Spreadsheet"
    )
    
    sheet = DynamicChoiceField(
        choices=[("", "-- Select Sheet --")],
        required=True,
        help_text="Select a sheet within the spreadsheet"
    )
    
    row_number = forms.IntegerField(
        min_value=1,
        required=True,
        help_text="Row number to retrieve (1-indexed)"
    )
    
    header_row = forms.IntegerField(
        min_value=1,
        initial=1,
        required=True,
        help_text="Row containing column headers (default: 1)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate Google account choices from backend API
        self.fields['google_account'].choices = get_google_account_choices()
    
    def get_field_dependencies(self):
        """
        Define cascading field dependencies.
        
        Returns:
            Dict mapping parent field -> list of dependent fields
        """
        return {
            'google_account': ['spreadsheet'],  # Account selection loads spreadsheets
            'spreadsheet': ['sheet']            # Spreadsheet selection loads sheets
        }
    
    def populate_field(self, field_name, parent_value, form_values=None):
        """
        Provide choices for dependent fields based on parent value.
        
        Called by the form dependency system when a parent field changes.
        
        Args:
            field_name: Name of the dependent field to populate
            parent_value: Value of the immediate parent field
            form_values: All current form values for multi-parent access
            
        Returns:
            List of (value, text) tuples for the field choices
        """
        from .services.google_sheets_service import GoogleSheetsService
        
        form_values = form_values or {}
        
        if field_name == 'spreadsheet':
            # Load spreadsheets for the selected Google account
            if not parent_value:
                return [("", "-- Select Spreadsheet --")]
            
            try:
                service = GoogleSheetsService(parent_value)
                spreadsheets = service.list_spreadsheets()
                
                logger.debug(
                    "Populated spreadsheets",
                    account_id=parent_value,
                    count=len(spreadsheets)
                )
                
                return [("", "-- Select Spreadsheet --")] + list(spreadsheets)
                
            except Exception as e:
                logger.error(
                    "Failed to load spreadsheets",
                    account_id=parent_value,
                    error=str(e)
                )
                return [("", "-- Error loading spreadsheets --")]
        
        elif field_name == 'sheet':
            # Load sheets for the selected spreadsheet
            if not parent_value:
                return [("", "-- Select Sheet --")]
            
            try:
                # Get account ID from form_values (multi-parent access)
                account_id = form_values.get('google_account')
                
                if not account_id:
                    logger.warning("No account ID available for sheet loading")
                    return [("", "-- Select account first --")]
                
                service = GoogleSheetsService(account_id)
                sheets = service.list_sheets(parent_value)
                
                logger.debug(
                    "Populated sheets",
                    spreadsheet_id=parent_value,
                    account_id=account_id,
                    count=len(sheets)
                )
                
                # Return sheet_name as value (needed for Sheets API calls)
                return [("", "-- Select Sheet --")] + [
                    (name, name) for sheet_id, name in sheets
                ]
                
            except Exception as e:
                logger.error(
                    "Failed to load sheets",
                    spreadsheet_id=parent_value,
                    error=str(e)
                )
                return [("", "-- Error loading sheets --")]
        
        return []

