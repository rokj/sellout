from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from common.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms

from pos.models import Company
from common.functions import has_permission, no_permission_view
from common import globals as g
from config.functions import set_user_value, get_user_value, get_company_value, set_company_value
from config.currencies import currency_choices

import pytz


########################
### helper functions ###
########################
def list_date_formats():
    """ lists first-level keys in g.DATE_FORMATS
        returns tuples for forms.ChoiceField
    
        could belong to ConfigForm, but will eventually be used in other parts of the app
    """
    return sorted([(key, key) for key in g.DATE_FORMATS])


def list_timezones():
    timezones = []
    for tz in pytz.common_timezones:
        # TODO: not tested
        timezones.append((tz, tz.replace('_', ' ')))
        
    return timezones


def list_time_formats():
    """ lists first-level keys in g.TIME_FORMATS (see list_date_formats) """
    return sorted([(key, key) for key in g.TIME_FORMATS])


#######################
### forms and views ###
#######################
class ConfigForm(forms.Form):
    decimal_places_choices = (
        (0, '0'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
    )

    date_format = forms.ChoiceField(choices=list_date_formats(), required=True)
    time_format = forms.ChoiceField(choices=list_time_formats(), required=True)
    timezone = forms.ChoiceField(choices=list_timezones(), required=True)
    currency = forms.ChoiceField(choices=currency_choices, required=True)
    decimal_separator = forms.CharField(max_length=1, required=True)
    decimal_places = forms.ChoiceField(choices=decimal_places_choices, required=True)

    bill_serial_format = forms.ChoiceField(g.BILL_FORMAT_OPTIONS)

    payment_bitcoin_address = forms.CharField(help_text=_("where bitcoins will be resend from our bitcoin wallet after user sends bitcoins (after 3 confirmations)"), max_length=34, required=False)
    payment_paypal_address = forms.CharField(label=_('Paypal email address'), help_text=_("where funds will be sent to when using paypal payment method; this MUST be PAYPAL VERIFIED BUSINESS account"), max_length=34, required=False)

    def clean_decimal_places(self):
        data = self.cleaned_data['decimal_places']

        try:
            return int(data)
        except (TypeError, ValueError):
            return 2


class UserForm(forms.Form):
    button_sizes = [(key, key) for key, value in g.PRODUCT_BUTTON_DIMENSIONS.iteritems()]

    product_button_size = forms.ChoiceField(choices=button_sizes)
    product_display = forms.ChoiceField((("box", _("In boxes")), ("line", _("In lines"))), required=True)
    # currently disabled
    # display_breadcrumbs = forms.BooleanField(required=False,
    #                                          widget=forms.Select(choices=((True, _("Yes")), (False, _("No")))))


@login_required
def company_settings(request, company):
    c = get_object_or_404(Company, url_name=company)

    # permissions
    if not has_permission(request.user, c, 'config', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit system configuration."))

    # get config: specify initial data manually (also for security reasons,
    # to not accidentally include secret data in request.POST or whatever)

    # this may be a little wasteful on resources, but config is only edited once in a lifetime or so
    # get_value is needed because dict['key'] will fail if new keys are added but not yet saved
    initial = {
        'date_format': get_company_value(request.user, c, 'pos_date_format'),
        'time_format': get_company_value(request.user, c, 'pos_time_format'),
        'timezone': get_company_value(request.user, c, 'pos_timezone'),
        'currency': get_company_value(request.user, c, 'pos_currency'),
        'decimal_separator': get_company_value(request.user, c, 'pos_decimal_separator'),
        'decimal_places': get_company_value(request.user, c, 'pos_decimal_places'),
        'payment_bitcoin_address': get_company_value(request.user, c, 'pos_payment_bitcoin_address'),
        'payment_paypal_address': get_company_value(request.user, c, 'pos_payment_paypal_address'),
        'bill_serial_format': get_company_value(request.user, c, 'pos_bill_serial_format')
    }

    if request.method == 'POST':
        try:
            form = ConfigForm(request.POST)
            if form.is_valid():
                for key in initial:
                    print "%s: %s" % ("pos_" + key, form.cleaned_data[key])
                    set_company_value(request.user, c, "pos_" + key, form.cleaned_data[key])
            else:
                print form.errors
        except Exception as e:
            print e

    else:
        form = ConfigForm(initial=initial)  # An unbound form

    context = {
        'company': c,
        'form': form,
        'title': _("System configuration"),
        'site_title': g.MISC['site_title'],
    }

    return render(request, 'pos/manage/config.html', context)


@login_required
def user_settings(request, company):
    c = get_object_or_404(Company, url_name=company)

    # permissions
    if not has_permission(request.user, c, 'config', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit system configuration."))

    # get config: specify initial data manually (also for security reasons,
    # to not accidentally include secret data in request.POST or whatever)

    # this may be a little wasteful on resources, but config is only edited once in a lifetime or so
    # get_value is needed because dict['key'] will fail if new keys are added but not yet saved
    initial = {
        'product_button_size': get_user_value(request.user, 'pos_product_button_size'),
        'product_display': get_user_value(request.user, 'pos_product_display'),
        'display_breadcrumbs': get_user_value(request.user, 'pos_display_breadcrumbs'),
    }

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            for key in initial:
                set_user_value(request.user, "pos_" + key, form.cleaned_data[key])
    else:
        form = UserForm(initial=initial)  # An unbound form

    context = {
        'company': c,
        'form': form,
        'title': _("User settings"),
        'site_title': g.MISC['site_title'],
    }

    return render(request, 'pos/manage/user.html', context)