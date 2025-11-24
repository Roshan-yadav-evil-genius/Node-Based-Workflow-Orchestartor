import os
import django
from django.conf import settings

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

from django import forms
from rich import print
import json
from field_parser import parse_field_to_json

FRUIT_CHOICES = [
    ('apple', 'Apple'),
    ('banana', 'Banana'),
    ('orange', 'Orange'),
    ('mango', 'Mango'),
]

class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)

    fruit = forms.ChoiceField(choices=[])  # temporary

    def __init__(self, *args, **kwargs):
        dynamic_choices = kwargs.pop("fruit_choices", None)
        super().__init__(*args, **kwargs)

        if dynamic_choices:
            self.fields["fruit"].choices = dynamic_choices


form = ContactForm()
form_state=[]
for x in form:
    print("Label: ", x.label_tag())
    print("Input: ", str(x).replace("\n", " "))
    print("Error: ", x.errors)
    field_json = parse_field_to_json(x)
    form_state.append(field_json)
print(form_state)
FRUIT_CHOICES.append(("apple1","Appel 1"))
form = ContactForm(data=dict(subject="mouse",fruit="apple12"),fruit_choices=FRUIT_CHOICES)
form_state=[]
for x in form:
    print("Label: ", x.label_tag())
    print("Input: ", str(x).replace("\n", " "))
    print("Error: ", x.errors)
    field_json = parse_field_to_json(x)
    form_state.append(field_json)
print(form_state)