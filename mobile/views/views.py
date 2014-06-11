from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from common.globals import UNITS
from config.functions import get_config, get_value
from pos.models import Company, Tax
from pos.views.manage.category import get_all_categories
from pos.views.manage.discount import JSON_discounts, get_all_discounts
from pos.views.manage.tax import get_taxes, tax_to_dict
from pos.views.util import JSON_error, has_permission, JSON_response, JSON_ok
from django.utils.translation import ugettext as _



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_units(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    units = UNITS
    result = {'units': units}
    return JSON_response(result)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_cut(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    if not has_permission(request.user, c, 'tax', 'list'):
        return JSON_error(_("You have no permission to view taxes"))

    taxes = Tax.objects.filter(company=c)
    result = {}
    r = []
    for t in taxes:
        r.append(tax_to_dict(request.user, t))
    result['taxes'] = r

    units = UNITS
    result['units'] = units

    categories = get_all_categories(c.id, json=True)
    result['categories'] = categories

    discounts = get_all_discounts(request.user, c, android=True)
    result['discounts'] = discounts

    result['config'] = get_config_attrs(request.user)

    return JSON_response(result)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def get_mobile_config(request, company):
    return JSON_ok(extra=get_config_attrs(request.user))


def get_config_attrs(user):

    dict = {'user_id': user.id,
            'pos_decimal_separator': get_value(user, 'pos_decimal_separator'),
            'pos_decimal_places': get_value(user, 'pos_decimal_places'),
            'pos_discount_calculation': get_value(user, 'pos_discount_calculation')
    }
    return dict