import django
from django.conf import settings
from django import forms

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

class ContactForm(forms.Form):
    # subject = forms.CharField(max_length=100)
    # message = forms.CharField(widget=forms.Textarea)
    # sender = forms.EmailField()
    # cc_myself = forms.BooleanField(required=False)
    COUNTRY_DATA=[
        ("india","India"),
        ("usa","USA")
    ]
    # Base fields with empty choices — we will fill these in __init__
    country = forms.ChoiceField(choices=COUNTRY_DATA )
    state = forms.ChoiceField(choices=[])
    language = forms.ChoiceField(choices=[])