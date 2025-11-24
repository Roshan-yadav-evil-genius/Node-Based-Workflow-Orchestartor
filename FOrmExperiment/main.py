from rich import print
from FormSerializer import FormSerializer
from ContactForm import ContactForm


form = ContactForm()
print(FormSerializer(form).to_json(),end="-"*20)


form.update_field('country', 'india')  # Populates states
print(FormSerializer(form).to_json(),end="-"*20)

form.update_field('state', 'maharashtra')  # Populates languages
print(FormSerializer(form).to_json(),end="-"*20)

form.update_field('language', 'marathi1')  # Populates languages
print(FormSerializer(form).to_json(),end="-"*20)