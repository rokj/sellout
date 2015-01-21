from django.http import JsonResponse
from django.utils.translation import ugettext as _
from django.db.models import Q

from pos.models import Company, Category, Discount, Product, ProductDiscount, Price, PurchasePrice, Tax
from pos.views.manage.product import JSON_units, get_product, search_products, create_product, edit_product, \
    delete_product, product_to_dict, toggle_favorite, get_product_, search_products_, create_product_, edit_product_, \
    delete_product_, toggle_favorite_
from common.functions import JsonError, \
                            has_permission
from rest_framework.decorators import api_view, permission_classes,\
    authentication_classes
from rest_framework.permissions import IsAuthenticated

###############
## products ###
###############

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_JSON_units(request, company_id):
    return JSON_units(request, company_id)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_product(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return get_product_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_search_products(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return search_products_(request, c, android=True)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_create_product(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return create_product_(request, c, android=True)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_product(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return edit_product_(request, c, android=True)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_prodcut(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return delete_product_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_products(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    if not has_permission(request.user, c, 'product', 'view'):
        return JsonError(_("You have no permission to view taxes"))

    products = Product.objects.filter(company=c)

    r = []
    for p in products:
        r.append(product_to_dict(request.user, c,  p, android=True))

    return JsonResponse(r, safe=False)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_toggle_favorite(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    return toggle_favorite_(request, c)