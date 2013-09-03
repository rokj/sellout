# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: product

from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db.models import Q

from pos.models import Company, Discount, Product, Price
from pos.views.util import error, JSON_response, JSON_parse, resize_image, validate_image

from pos.views.manage.category import get_all_categories, JSON_categories
from pos.views.manage.discount import is_discount_valid, discount_to_dict, JSON_discounts

from common import globals as g

from decimal import Decimal
from datetime import date


###############
## products ###
###############
def JSON_units(request, company):
    # at the moment, company is not needed
    return JSON_response(g.UNITS); # G units!
    
def products(request, company):
    company = get_object_or_404(Company, url_name = company)
    
    context = {
               'company':company, 
               # TODO add title & site title
               }
    return render(request, 'pos/manage/products.html', context)

def product_to_dict(p, company):
    # returns all relevant product's data
    ret = {}
    
    ret['id'] = p.id
    
    try: # only the last price from the price table
        price = Price.objects.filter(product__id=p.id).order_by('-date_updated')[0]
        price = str(price.unit_price)
    except:
        price = ''
        pass
    
    ret['price'] = price
    
    # all discounts in a list
    discounts = {}
    for d in p.discount.all():
        discounts[str(d.id)] = discount_to_dict(d)

    ret['discounts'] = discounts
    
    # check if product's image exists
    # TODO: better image handling
    if p.image:
        ret['image'] = p.image.url
    
    # category?
    if p.category:
        ret['category'] = p.category.name
    
    if p.code:
        ret['code'] = p.code
    if p.shop_code:
        ret['shop_code'] = p.shop_code
    if p.name:
        ret['name'] = p.name
    if p.description:
        ret['description'] = p.description
    if p.private_notes:
        ret['private_notes'] = p.private_notes
    if p.unit_type:
        ret['unit_type'] = p.unit_type
    if p.tax:
        ret['tax'] = str(p.tax)
    if p.stock:
        ret['stock'] = p.stock
    
    # edit and delete urls
    ret['edit_url'] = reverse('pos:edit_product', args=[company.url_name, p.id]) 
    
    return ret

def search_products(request, company):
    company = get_object_or_404(Company, url_name = company)
    
    # get all products from this company and filter them by entered criteria
    products = Product.objects.filter(company=company)
    
    criteria = JSON_parse(request.POST['data'])
    
    # filter by: ("advanced" values in criteria dict)
    # name_filter
    if criteria.get('name_filter'):
        filter_by_name = True
        products = products.filter(name__icontains=criteria.get('name_filter'))
    else:
        filter_by_name = False

    # product_code_filter
    if criteria.get('product_code_filter'):
        filter_by_product_code = True
        products = products.filter(product_code__icontains = criteria.get('product_code_filter'))
    else:
        filter_by_product_code = False
    
    # shop_code_filter
    if criteria.get('shop_code_filter'):
        filter_by_shop_code = True
        products = products.filter(shop_code__icontains = criteria.get('shop_code_filter'))
    else:
        filter_by_shop_code = False
    
    # notes_filter
    if criteria.get('notes_filter'):
        filter_by_notes = True
        products = products.filter(private_notes__icontains = criteria.get('notes_filter'))
    else:
        filter_by_notes = False
        
    # description_filter
    if criteria.get('description_filter'):
        filter_by_description = True
        products = products.filter(description__icontains = criteria.get('description_filter'))
    else:
        filter_by_description = False
        
    # category_list_filter
    if criteria.get('category_filter'):
        filter_by_category = True
        products = products.filter(category__id = int(criteria.get('category_filter')))
    else:
        filter_by_category = False
        
    # tax_filter
    if criteria.get('tax_filter'):
        #filter_by_tax = True
        products = products.filter(tax = Decimal(criteria.get('tax_filter')))
    else:
        pass
        #filter_by_tax = False
    
    # price_filter
    if criteria.get('price_filter'):
        try:
            products = products.filter(pk__in=Price.objects.filter(unit_price=Decimal(criteria.get('price_filter'))).order_by('-date_updated')[:1])
            #filter_by_price = True
        except Price.DoesNotExist:
            pass
            #filter_by_price = False
    else:
        pass
        #filter_by_price = False

    # discount
    if criteria.get('discount_filter'):
        #filter_by_discount = True
        products = products.filter(discount__code=criteria.get('discount_filter'))
    else:
        pass
        #filter_by_discount = False

    # general filter: search all fields that have not been searched yet 
    general_filter = criteria['general_filter'].split(' ')
    #g_products = Product.objects.none()

    for w in general_filter:
        if w == '':
            continue
        
        # search categories, product_code, shop_code, name, description, notes,
        # but only if it wasn't entered in the "advanced" filter
        # assemble the Q() filter
        f = Q()
        if not filter_by_name:
            f = f | Q(name__icontains=w)
        if not filter_by_product_code:
            f = f | Q(code__icontains=w)
        if not filter_by_shop_code:
            f = f | Q(shop_code__icontains=w)
        if not filter_by_notes:
            f = f | Q(private_notes__icontains=w)
        if not filter_by_description:
            f = f | Q(description__icontains=w)
        if not filter_by_category:
            f = f | Q(category__name=w)

        if f:
            products = products.filter(f)
        # omit search by tax, price, discount

    products = products.distinct().order_by('name')
    
    # return serialized products
    ps = []
    for p in products:
        ps.append(product_to_dict(p, company))

    return JSON_response(ps);

