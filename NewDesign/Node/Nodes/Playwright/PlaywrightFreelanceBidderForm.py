from ...Core.Form.Core.BaseForm import BaseForm
from django.forms import IntegerField, URLField, FloatField, CharField
from django.forms.widgets import Textarea


class PlaywrightFreelanceBidderForm(BaseForm):
    project_url = URLField()
    bid_amount = FloatField()
    estimated_delivery_days = IntegerField(help_text="No of days to complete the project")
    proposal = CharField(
        widget=Textarea(),
        help_text="Write a proposal for the project",
        # min_length=100,
        max_length=1000
    )