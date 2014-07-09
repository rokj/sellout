# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: categories
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms

from pos.models import Company
from pos.views.util import has_permission, no_permission_view
from common import globals as g
from config.functions import set_user_value, get_user_value, get_company_value

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
        timezones.append((tz, tz))
        
    return timezones


def list_time_formats():
    """ lists first-level keys in g.TIME_FORMATS (see list_date_formats)
    """
    return sorted([(key, key) for key in g.TIME_FORMATS])


#######################
### forms and views ###
#######################
class ConfigForm(forms.Form):
    button_sizes = [(key, key) for key, value in g.PRODUCT_BUTTON_DIMENSIONS.iteritems()]
    decimal_places_choices = (
        ('0', 0),
        ('1', 1),
        ('2', 2),
        ('3', 3),
        ('4', 4),
    )

    date_format = forms.ChoiceField(choices=list_date_formats(), required=True)
    time_format = forms.ChoiceField(choices=list_time_formats(), required=True)
    timezone = forms.ChoiceField(choices=list_timezones(), required=True)
    currency = forms.CharField(max_length=4, required=True)
    discounts_per_page = forms.IntegerField(required=True)
    decimal_separator = forms.CharField(max_length=1, required=True)
    decimal_places = forms.ChoiceField(choices=decimal_places_choices, required=True)
    interface_product_button_size = forms.ChoiceField(choices=button_sizes, label=_("Product button size"))
    discount_calculation = forms.ChoiceField(g.DISCOUNT_CALCULATION, required=True)
    product_display = forms.ChoiceField((("box", _("In boxes")), ("line", _("In lines"))), required=True)
    display_breadcrumbs = forms.BooleanField(required=False,
                                             widget=forms.Select(choices=((True, _("Yes")), (False, _("No")))))


@login_required
def edit_config(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # permissions
    if not has_permission(request.user, c, 'config', 'edit'):
        return no_permission_view(request, c, _("visit this page"))
    
    # get config: specify initial data manually (also for security reasons,
    # to not accidentally include secret data in request.POST or whatever)
    
    # this may be a little wasteful on resources, but config is only edited once in a lifetime or so
    # get_value is needed because dict['key'] will fail if new keys are added but not yet saved
    initial = {
        'date_format': get_company_value(request.user, c, 'pos_date_format'),
        'time_format': get_company_value(request.user, c, 'pos_time_format'),
        'timezone': get_company_value(request.user, c, 'pos_timezone'),
        'currency': get_company_value(request.user, c, 'pos_currency'),
        'discounts_per_page': get_user_value(request.user, 'pos_discounts_per_page'),
        'decimal_separator': get_company_value(request.user, c, 'pos_decimal_separator'),
        'interface_product_button_size': get_user_value(request.user, 'pos_interface_product_button_size'),
        'discount_calculation': get_company_value(request.user, c, 'pos_discount_calculation'),
        'decimal_places': get_company_value(request.user, c, 'pos_decimal_places'),
        'product_display': get_user_value(request.user, 'pos_product_display'),
        'display_breadcrumbs': get_user_value(request.user, 'pos_display_breadcrumbs'),
    }
    
    if request.method == 'POST':
        form = ConfigForm(request.POST)
        if form.is_valid():
            for key in initial:
                set_user_value(request.user, "pos_" + key, form.cleaned_data[key])
    else:
        form = ConfigForm(initial=initial)  # An unbound form

    context = {
        'company': c,
        'form': form,
        'title': _("System configuration"),
        'site_title': g.MISC['site_title'],
    }

    return render(request, 'pos/manage/config.html', context)
