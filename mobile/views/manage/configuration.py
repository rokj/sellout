
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from config.functions import get_company_value, set_company_value
from pos.models import Company, Tax
from pos.views.util import JsonError, has_permission, JsonOk, no_permission_view, JsonParse
from django.utils.translation import ugettext as _



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def get_mobile_config(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'config', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit system configuration."))

    return JsonOk(extra=get_company_config(request.user, Company.objects.get(url_name=company)))


def get_company_config(user, company):
    return {
        'company_id': company.id,
        'pos_decimal_separator': get_company_value(user, company, 'pos_decimal_separator'),
        'pos_decimal_places': get_company_value(user, company, 'pos_decimal_places'),
        'pos_discount_calculation': get_company_value(user, company, 'pos_discount_calculation'),
        'pos_time_format': get_company_value(user, company, 'pos_time_format'),
        'pos_date_format': get_company_value(user, company, 'pos_date_format'),
        'pos_timezone': get_company_value(user, company, 'pos_timezone'),
        'pos_currency': get_company_value(user, company, 'pos_currency'),
    }


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def save_company_config(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'config', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit system configuration."))

    data = JsonParse(request.POST['data'])

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
        'discount_calculation': get_company_value(request.user, c, 'pos_discount_calculation'),
    }

    for key in data:
        set_company_value(request.user, c, key, data[key])

    return JsonOk(extra=get_company_config(request.user, Company.objects.get(url_name=company)))
