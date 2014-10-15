# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from common.globals import UNITS
from config.functions import get_company_value, set_company_value
from pos.models import Company, Tax
from pos.views.manage.category import get_all_categories
from pos.views.manage.configuration import ConfigForm
from pos.views.manage.discount import get_all_discounts
from pos.views.manage.tax import tax_to_dict
from pos.views.util import JsonError, has_permission, JsonOk, no_permission_view, JsonParse
from django.utils.translation import ugettext as _


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_units(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    units = UNITS
    result = {'units': units}
    return JsonResponse(result)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_cut(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    if not has_permission(request.user, c, 'tax', 'view'):
        return JsonError(_("You have no permission to view taxes"))

    taxes = Tax.objects.filter(company=c)
    result = {}
    r = []
    for t in taxes:
        r.append(tax_to_dict(request.user, c, t))
    result['taxes'] = r

    units = UNITS
    result['units'] = units

    categories = get_all_categories(c, json=True)
    result['categories'] = categories

    discounts = get_all_discounts(request.user, c, android=True)
    result['discounts'] = discounts


    return JsonResponse(result)
