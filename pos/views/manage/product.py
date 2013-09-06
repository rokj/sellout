# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: product

from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db.models import Q

from pos.models import Company, Category, Discount, Product, Price
from pos.views.util import error, JSON_response, JSON_parse, JSON_error, JSON_ok

from pos.views.manage.category import get_all_categories, JSON_categories
from pos.views.manage.discount import is_discount_valid, discount_to_dict, JSON_discounts

from common import globals as g

import datetime as dtm
import decimal as d


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
        'title':_("Products"),
        'site_title':g.MISC['site_title'],
    }
    return render(request, 'pos/manage/products.html', context)

def product_to_dict(p):
    # returns all relevant product's data:
    # id
    # price - numeric value
    # unit type
    # discounts - dictionary or all discounts for this product 
    #    (see discounts.discount_to_dict for details)
    # image - TODO
    # category - name
    # code
    # shop code
    # description
    # private notes
    # tax
    # stock
    # edit url
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
    for d in p.discounts.all():
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
        ret['stock'] = str(p.stock)
    
    # edit and delete urls
    ret['get_url'] = reverse('pos:get_product', args=[p.company.url_name, p.id])
    ret['edit_url'] = reverse('pos:edit_product', args=[p.company.url_name, p.id])
    ret['delete_url'] = reverse('pos:delete_product', args=[p.company.url_name, p.id]) 
    
    return ret

def show_product(request, company, product_id):
    company = get_object_or_404(Company, url_name = company)
    product = get_object_or_404(Product, id = product_id, company = company)
    
    return JSON_response(product_to_dict(product))
    
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
        products = products.filter(tax = d.Decimal(criteria.get('tax_filter')))
    else:
        pass
        #filter_by_tax = False
    
    # price_filter
    if criteria.get('price_filter'):
        try:
            products = products.filter(pk__in=Price.objects.filter(unit_price=d.Decimal(criteria.get('price_filter'))).order_by('-date_updated')[:1])
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
        ps.append(product_to_dict(p))

    return JSON_response(ps);

def validate_product(data):
    # data format (*-validation needed):
    # id
    # price - numeric value*
    # unit type
    # discounts - list of discount ids
    # image - TODO
    # category - id
    # code
    # shop code
    # description
    # private notes
    # tax*
    # stock*
    def r(status, msg):
        return {'status':status,
            'data':data,
            'message':msg}

    # return:
    # {status:true/false - if cleaning succeeded
    #  data:cleaned_data - empty dict if status = false
    #  message:error_message - empty if status = true
    
    # price
    try:
        data['price'] = d.Decimal(data['price'])
    except:
        return r(False, _("Check price notation"))
        
    # unit type (probably doesn't need checking
    if not data['unit_type'] in dict(g.UNITS):
        return r(False, _("Invalid unit type"))

    # image: todo
    
    # code, shop code, description, notes - anything can be entered
    try:
        data['tax'] = d.Decimal(data['tax'])
    except:
        return r(False, _("Check tax notation"))
    
    try:
        data['stock'] = d.Decimal(data['stock'])
    except:
        return r(False, _("Check stock notation"))
    
    return {'status':True, 'data':data} 
    
def create_product(request, company):
    pass

def edit_product(request, company, product_id):
    # update existing product
    company = get_object_or_404(Company, url_name = company)
    data = JSON_parse(request.POST['data'])
    
    # see if product exists in database
    try:
        product = Product.objects.get(id=product_id)
    except:
        return JSON_error(_("Product does not exist"))
    
    # TODO: check for permissions
    
    # check if format is OK
    valid = validate_product(data)
    if not valid['status']:
        return JSON_error(valid['message'])
    data = valid['data']
    
    # update product
    product.price = data['price']
    product.unit_type = data['unit_type']

    # update discounts: remove deleted
    discounts = product.discounts.all();
    for d in discounts:
        if d.id not in data['discounts']:
            product.discounts.remove(d)
        else:
            data['discounts'].remove(d.id)

    # update discounts: add missing
    # anything that is left in data['discounts'] must be added
    for d in data['discounts']:
        try:
            discount = Discount.objects.get(id=int(d))
            product.discounts.add(discount)
        except Discount.DoesNotExist:
            pass

    # TODO: image
    try:
        category = Category.objects.get(id=data['category'])
        product.category = category
    except Category.DoesNotExist:
        pass # do not change product's category

    product.code = data['code']
    product.shop_code = data['shop_code']
    product.description = data['description']
    product.private_notes = data['private_notes']
    product.stock = data['stock']
    product.tax = data['tax']
    
    product.save()
    
    # price has to be updated separately
    product.update_price(request.user, data['price'])

    return JSON_ok();

def delete_product(request, company, product_id):
    pass