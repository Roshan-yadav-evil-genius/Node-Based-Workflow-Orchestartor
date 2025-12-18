from ...Core.Form.Core.BaseForm import BaseForm
from django.forms import CharField, URLField, ChoiceField

class WebPageLoaderForm(BaseForm):
    url = URLField(
        required=True, 
        help_text="URL to load. If empty, uses 'url' from input data."
    )
    session_name = CharField(
        required=True, 
        initial="default", 
        help_text="Name of the persistent browser context/session."
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
