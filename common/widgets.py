from django.forms.widgets import ClearableFileInput, CheckboxInput
from django.utils.translation import ugettext as _
from django.utils.html import format_html, conditional_escape
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe


# hide the 'currently' text for file inputs
# Kudos: http://stackoverflow.com/questions/17293627/hide-django-clearablefileinput-checkbox
class PlainClearableFileInput(ClearableFileInput):
    template_with_initial = '%(input)s %(clear_template)s'

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': '',
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }
        template = '%(input)s'
        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['initial'] = format_html(self.url_markup_template,
                                                   value.url,
                                                   force_text(value))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = \
                    CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id, 'class': 'clear'})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)