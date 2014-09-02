from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from pos.models import Company
from pos.views.manage.tax import list_taxes, get_all_taxes, edit_tax, delete_tax, \
    set_default_tax  #, get_taxes, save_taxes
from pos.views.util import JSON_error, JSON_ok
from django.utils.translation import ugettext as _


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_list_taxes(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    taxes = get_all_taxes(request.user, c)

    return JSON_ok(extra=taxes)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_tax(request, company):
    return edit_tax(request, company)



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_tax(request, company):
    return delete_tax(request, company)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def mobile_save_default_tax(request, company):
    return set_default_tax(request, company)

#@api_view(['GET', 'POST'])
#@permission_classes((IsAuthenticated,))
#def mobile_get_taxes(request, company):
#    return get_taxes(request, company)
#
#@api_view(['GET', 'POST'])
#@permission_classes((IsAuthenticated,))
#def mobile_save_taxes(request, company):
#    return save_taxes(request, company)
