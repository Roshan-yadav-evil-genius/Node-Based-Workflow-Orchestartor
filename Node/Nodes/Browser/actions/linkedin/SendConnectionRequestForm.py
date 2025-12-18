from .....Core.Form.Core.BaseForm import BaseForm
from django.forms import CharField, BooleanField


class SendConnectionRequestForm(BaseForm):
    profile_url = CharField(
        required=True,
        help_text="LinkedIn profile URL. If empty, uses the current page URL from the browser session."
    )
    session_name = CharField(
        required=True,
        initial="default",
        help_text="Name of the persistent browser context/session."
    )
    send_connection_request = BooleanField(
        required=False,
        initial=True,
        help_text="Send a connection request to the profile."
    )
    follow = BooleanField(
        required=False,
        initial=True,
        help_text="Follow the profile."
    )
