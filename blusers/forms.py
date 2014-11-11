# -*- coding:utf-8 -*-
from django.forms import Select
from django.utils.translation import ugettext_lazy as _
from django import forms
from blusers.models import BlocklogicUser
from blusers.models import UserProfile

import re
from common.globals import SEX
from common.globals import TAX_PAYER_CHOICES
from common.models import Country

FIRST_LAST_NAME_REGEX = re.compile(r"^[\w ]+$", re.U)

class LoginForm(forms.ModelForm):
    """
    So we do not really want to fuck around with overriding methods and iterating
    and changing passed arguments in super class, so we KISS and do it this way.

    Copied from django.contrib.auth.forms.py and changed a bit.

    A form that creates a user, with no privileges, from the given data.
    """

    email = forms.EmailField(label=_("E-mail"), required=True, max_length=75,
                             help_text=_("Required field. 75 characters or fewer. Letters, digits and @/./+/-/_ characters only."),
                             error_messages={'invalid': _("This value may contain only letters, digits and characters @/./+/-/_.")})
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, required=False)

    class Meta:
        model = BlocklogicUser
        fields = ("email", "password")

    def clean_email(self):
        """
        Validates that a user exists with the given e-mail address.
        """
        email = self.cleaned_data["email"]
        self.users_cache = BlocklogicUser.objects.filter(email__iexact=email)

        if len(self.users_cache) == 0:
            raise forms.ValidationError(_("User with this email does not exist. Maybe you misspelled it?"))

        return self.cleaned_data["email"]

    def set_request(self, request):
        self.request = request