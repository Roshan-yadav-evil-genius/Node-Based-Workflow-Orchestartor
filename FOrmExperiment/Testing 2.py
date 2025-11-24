from rich import print
from field_parser import parse_field_to_json
from Model import ContactForm


# form = ContactForm()
# form_state=[]
# for x in form:
#     print("Label: ", x.label_tag())
#     print("Input: ", str(x).replace("\n", " "))
#     print("Error: ", x.errors)
#     field_json = parse_field_to_json(x)
#     form_state.append(field_json)
# print(form_state)

form = ContactForm(data=dict(country="india",state="maharashtra1"))

form_state=[]
for x in form:
    field_json = parse_field_to_json(x)
    form_state.append(field_json)
print(form_state)