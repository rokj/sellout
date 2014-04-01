from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db.models import Q

from pos.models import Company, Category, Discount, Product, ProductDiscount, Price, PurchasePrice, Tax
from pos.views.manage.product import JSON_units, get_product, search_products, create_product, edit_product, \
    delete_product
from pos.views.util import error, JSON_response, JSON_parse, JSON_error, JSON_ok, \
                           has_permission, no_permission_view, \
                           format_number, parse_decimal, image_dimensions, \
                           image_from_base64, max_field_length
from pos.views.manage.discount import discount_to_dict
from pos.views.manage.category import get_subcategories
from pos.views.manage.tax import get_default_tax

from common import globals as g
from config.functions import get_value

import decimal
from sorl.thumbnail import get_thumbnail
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
    return search_products(request, company)



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_create_product(request, company):
    return create_product(request, company)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_product(request, company):
    return edit_product(request, company)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_prodcut(request, company):
    return delete_product(request, company)
