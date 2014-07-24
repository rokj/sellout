from django.utils.translation import ugettext as _
from django.db.models import Q

from pos.models import Company, Category, Discount, Product, ProductDiscount, Price, PurchasePrice, Tax
from pos.views.manage.product import JSON_units, get_product, search_products, create_product, edit_product, \
    delete_product, product_to_dict, toggle_favorite
from pos.views.util import JSON_response, JSON_error, \
                            has_permission
from rest_framework.decorators import api_view, permission_classes,\
    authentication_classes
from rest_framework.permissions import IsAuthenticated

###############
## products ###
###############

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_JSON_units(request, company):
    return JSON_units(request, company)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_product(request, company, product_id):
    return get_product(request, company, product_id)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_search_products(request, company):
    return search_products(request, company, android=True)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_create_product(request, company):
    return create_product(request, company, android=True)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_product(request, company):
    return edit_product(request, company, android=True)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_prodcut(request, company):
    return delete_product(request, company)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_products(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    if not has_permission(request.user, c, 'tax', 'view'):
        return JSON_error(_("You have no permission to view taxes"))

    products = Product.objects.filter(company=c)

    r = []
    for p in products:
        r.append(product_to_dict(request.user, c,  p, android=True))

    return JSON_response(r)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_product_discounts(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    if not has_permission(request.user, c, 'tax', 'list'):
        return JSON_error(_("You have no permission to view taxes"))

    products = Product.objects.filter(company=c)

    r = []
    for p in products:
        r.append(product_to_dict(request.user, p, android=True))

    return JSON_response(r)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_toggle_favorite(request, company):
    return toggle_favorite(request, company)