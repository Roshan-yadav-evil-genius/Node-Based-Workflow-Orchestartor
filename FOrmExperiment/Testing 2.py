from rich import print
from field_parser import parse_field_to_json
from Model import ContactForm


form = ContactForm()
form_state=[]
for x in form:
    field_json = parse_field_to_json(x)
    form_state.append(field_json)
print(form_state,end="-"*20)

form.update_field('country', 'india')  # Populates states
form_state=[]
for x in form:
    field_json = parse_field_to_json(x)
    form_state.append(field_json)
print(form_state,end="-"*20)

form.update_field('state', 'maharashtra')  # Populates languages
form_state=[]
for x in form:
    field_json = parse_field_to_json(x)
    form_state.append(field_json)
print(form_state,end="-"*20)
