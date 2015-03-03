# -*- coding:utf-8 -*-
from captcha.fields import CaptchaField
from django.utils.translation import ugettext_lazy as _
from django import forms
from blusers.models import BlocklogicUser

import re
from common.globals import SEX

import config.countries as countries

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

    """
    def clean_email(self):
        Validates that a user exists with the given e-mail address.

        email = self.cleaned_data["email"]
        self.users_cache = BlocklogicUser.objects.filter(email__iexact=email)

        if len(self.users_cache) == 0:
            raise forms.ValidationError(_("User with this email does not exist. Maybe you misspelled it?"))

        return self.cleaned_data["email"]
    """

    def set_request(self, request):
        self.request = request


class ResetPasswordForm(forms.Form):
    new_password_1 = forms.CharField(
        label=_("Enter new password"),
        required=True, widget=forms.PasswordInput)
    new_password_2 = forms.CharField(
        label=_("Enter new password again"),
        required=True, widget=forms.PasswordInput)
    key = forms.CharField(required=True, widget=forms.HiddenInput)

    def clean(self):
        if self.cleaned_data['new_password_1'] != self.cleaned_data['new_password_2']:
            raise forms.ValidationError(_("Passwords do not match."))

    def clean_key(self):
        if not BlocklogicUser.objects.filter(password_reset_key=self.cleaned_data['key']).exists():
            raise forms.ValidationError(_("Invalid password reset key"))

class BlocklogicUserForm(forms.ModelForm):
    """
    So we do not really want to fuck around with overriding methods and iterating
    and changing passed arguments in super class, so we KISS and do it this way.

    Copied from django.contrib.auth.forms.py and changed a bit.

    A form that creates a user, with no privileges, from the given data.
    """

    email = forms.EmailField(label=_("E-mail"), required=True, max_length=75,
                             help_text=_("Required field. 75 characters or fewer. Letters, digits and @/./+/-/_ characters only."),
                             error_messages={'invalid': _("This value may contain only letters, digits and characters @/./+/-/_.")})
    first_name = forms.RegexField(label=_("First name"), required=True, max_length=30, regex=FIRST_LAST_NAME_REGEX,
                                  help_text=_("Required field. 30 characters or fewer. Letters only and numbers only."),
                                  error_messages={'invalid': _("This value may contain only letters and numbers.")})
    last_name = forms.RegexField(label=_("Last name"), required=True, max_length=30, regex=FIRST_LAST_NAME_REGEX,
                                 help_text=_("Required field. 30 characters or fewer. Letters and numbers only."),
                                 error_messages={'invalid': _("This value may contain only letters and numbers.")})
    old_password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, required=False)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."), required=False)
    country = forms.ChoiceField(label=_("Country"), choices=countries.country_choices, required=True)
    sex = forms.CharField(label=_("Sex"), required=True, widget=forms.Select(choices=SEX, attrs={'class': 'sex'}))
    images = forms.FileField(label=_("Your photo"), required=False)

    captcha = CaptchaField()

    registration = True
    is_mobile = False

    class Meta:
        model = BlocklogicUser
        fields = ("email", "first_name", "last_name", "country", "images", "sex", )

    def clean_old_password(self):
        if not self.registration and self.request.POST.get('update_password', '') == "yes":
            old_password = self.cleaned_data.get('old_password', None)

            if not self.request.user.check_password(old_password):
                raise forms.ValidationError(_('Invalid old password.'))

        return self.cleaned_data["old_password"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]

        if len(password1) > 0 and len(password2) > 0:
            if password1 != password2:
                raise forms.ValidationError(_("The two password fields didn't match."))
        elif len(password1) > 0 or len(password2) > 0:
            if len(password1) != len(password2):
                raise forms.ValidationError(_("The two password fields didn't match."))

        return password2

    def clean_email(self):
        """
        Validates that a user exists with the given e-mail address.
        """
        if self.registration:
            email = self.cleaned_data["email"]
            self.users_cache = BlocklogicUser.objects.filter(email__iexact=email)

            if len(self.users_cache) != 0:
                raise forms.ValidationError(_("User with this email already exists. Maybe you should just try to login."))

            return email

        return self.cleaned_data["email"]

    def clean_images(self):
        """
        because of fucking bug like on:
        https://bitbucket.org/mlavin/django-selectable/issue/51/empty-m2m-field-with
        """

        if self.cleaned_data['images'] is None:
            return []

        return self.cleaned_data['images']

    def clean(self):
        # little hack
        # we need captcha only when creating user account

        # TODO: update this on user settings page (migrate from custom captcha to django-simple-captcha)

        #if self.is_mobile == False:
        #    if self.registration and self.instance.pk is None:
        #        if self.data and not self.request.POST['captcha_user_answer'] or ((int(self.request.session['captcha_answer']) != int(self.request.POST['captcha_user_answer']))):
        #            raise forms.ValidationError(_("It really is not that difficult."), "captcha_answer_error")

        return self.cleaned_data

    def set_request(self, request):
        self.request = request

class BlocklogicUserChangeForm(forms.ModelForm):
    last_name = forms.RegexField(label=_("Last name"), required=True, max_length=30, regex=FIRST_LAST_NAME_REGEX,
                                 help_text=_("Required field. 30 characters or fewer. Letters and numbers only."),
                                 error_messages={'invalid': _("This value may contain only letters and numbers.")},
                                 initial=_("Last"))
    old_password = forms.CharField(label=_("Password"), widget=forms.PasswordInput, required=False)
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label=_("Password confirmation"), widget=forms.PasswordInput,
                                help_text=_("Enter the same password as above, for verification."), required=False)
    country = forms.ChoiceField(label=("Country"), choices=countries.country_choices, required=True)
    sex = forms.CharField(required=True, max_length=6, widget=forms.RadioSelect(choices=SEX, attrs={'class': 'sex'}))
    images = forms.FileField(label=_("Your photo"), required=False)

    class Meta:
        model = BlocklogicUser
        fields = ("last_name", "country", "images", "sex",)

    def set_request(self, request):
        self.request = request

    def clean_old_password(self):
        if self.request.POST.get('update_password', '') == "yes":
            old_password = self.cleaned_data.get('old_password', None)

            if not self.request.user.check_password(old_password):
                raise forms.ValidationError(_('Invalid old password.'))

        return self.cleaned_data["old_password"]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]

        if len(password1) > 0 and len(password2) > 0:
            if password1 != password2:
                raise forms.ValidationError(_("The two password fields didn't match."))
        elif len(password1) > 0 or len(password2) > 0:
            if len(password1) != len(password2):
                raise forms.ValidationError(_("The two password fields didn't match."))

        return password2

    def clean_images(self):
        """
        because of fucking bug like on:
        https://bitbucket.org/mlavin/django-selectable/issue/51/empty-m2m-field-with
        """

        if self.cleaned_data['images'] is None:
            return []

        return self.cleaned_data['images']
