from ...Core.Form.Core.BaseForm import BaseForm
from django.forms import URLField, ChoiceField
import requests


def get_session_choices():
    """Fetch available browser session choices from backend API."""
    try:
        response = requests.get('http://127.0.0.1:7878/api/browser-sessions/choices/', timeout=5)
        if response.status_code == 200:
            sessions = response.json()
            # Return choices as (id, name) tuples
            return [(s['id'], s['name']) for s in sessions]
    except Exception:
        pass
    # Fallback to empty choices if API is unavailable
    return []


class WebPageLoaderForm(BaseForm):
    url = URLField(
        required=True, 
        help_text="URL to load. If empty, uses 'url' from input data."
    )
    session_name = ChoiceField(
        required=True,
        choices=[],  # Will be populated dynamically
        help_text="Select a persistent browser session."
    )
    wait_mode = ChoiceField(
        choices=[
            ('load', 'Load (Default)'),
            ('domcontentloaded', 'DOM Content Loaded'),
            ('networkidle', 'Network Idle')
        ],
        required=True,
        initial='load',
        help_text="Wait strategy for page loading."
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate session choices from backend API
        self.fields['session_name'].choices = get_session_choices()
