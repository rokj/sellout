
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from config.functions import get_company_value, set_company_value
from pos.models import Company, Tax
from common.functions import JsonError, has_permission, JsonOk, no_permission_view, JsonParse
from django.utils.translation import ugettext as _



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def get_mobile_config(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'config', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit system configuration."))

    return JsonOk(extra=company_config_to_dict(request.user, c))


def company_config_to_dict(user, company):
    return {
        'company_id': company.id,
        'pos_decimal_separator': get_company_value(user, company, 'pos_decimal_separator'),
        'pos_decimal_places': get_company_value(user, company, 'pos_decimal_places'),
        'pos_time_format': get_company_value(user, company, 'pos_time_format'),
        'pos_date_format': get_company_value(user, company, 'pos_date_format'),
        'pos_timezone': get_company_value(user, company, 'pos_timezone'),
        'pos_currency': get_company_value(user, company, 'pos_currency'),
        'pos_bill_serial_format': get_company_value(user, company, 'pos_bill_serial_format'),
        'pos_payment_bitcoin_address': get_company_value(user, company, 'pos_payment_bitcoin_address'),
        'pos_payment_paypal_address': get_company_value(user, company, 'pos_payment_paypal_address')
    }


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def save_company_config(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'config', 'edit'):
        return JsonError(_("You have no permission to edit system configuration."))

    data = JsonParse(request.POST['data'])

    for key in data:
        set_company_value(request.user, c, key, data[key])

    return JsonOk(extra=company_config_to_dict(request.user, c))
