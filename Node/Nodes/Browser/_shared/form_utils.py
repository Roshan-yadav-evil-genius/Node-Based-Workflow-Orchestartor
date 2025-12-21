"""Shared form utilities for browser-related nodes."""
import requests
from django.forms import ChoiceField


def get_session_choices():
    """Fetch available browser session choices from backend API."""
    try:
        response = requests.get('http://127.0.0.1:7878/api/browser-sessions/choices/', timeout=5)
        if response.status_code == 200:
            sessions = response.json()
            # Return choices as (id, name) tuples with a placeholder
            choices = [('', '-- Select Session --')]
            choices.extend([(s['id'], s['name']) for s in sessions])
            return choices
    except Exception:
        pass
    # Fallback to placeholder only if API is unavailable
    return [('', '-- Select Session --')]


class BrowserSessionField(ChoiceField):
    """
    A ChoiceField that automatically populates with available browser sessions.
    Use this in any browser-related form that needs a session dropdown.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', True)
        kwargs.setdefault('help_text', "Select a persistent browser session.")
        kwargs.setdefault('choices', [])
        super().__init__(*args, **kwargs)
        # Populate choices dynamically
        self.choices = get_session_choices()

