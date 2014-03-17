from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from pos.views.manage.tax import list_taxes, get_taxes, save_taxes


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_list_taxes(request, company):
    return list_taxes(request, company)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_taxes(request, company):
    return get_taxes(request, company)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_save_taxes(request, company):
    return save_taxes(request, company)
