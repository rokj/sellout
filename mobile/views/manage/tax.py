from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from pos.models import Company
from pos.views.manage.tax import list_taxes, get_all_taxes, edit_tax, delete_tax, \
    set_default_tax  #, get_taxes, save_taxes
from common.functions import JsonError, JsonOk
from django.utils.translation import ugettext as _


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_list_taxes(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    taxes = get_all_taxes(request.user, c)
    return JsonOk(extra=taxes)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_tax(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return edit_tax(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_tax(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return delete_tax(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def mobile_save_default_tax(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return set_default_tax(request, company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))
