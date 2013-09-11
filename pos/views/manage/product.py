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
from pos.views.util import error, JSON_response, JSON_parse, JSON_error, JSON_ok, \
                           has_permission, no_permission_view, \
                           format_number
from pos.views.manage.category import get_all_categories, JSON_categories
from pos.views.manage.discount import is_discount_valid, discount_to_dict, JSON_discounts

from common import globals as g
from config.functions import get_value

import datetime as dtm
import decimal as d
import pytz


###############
## products ###
###############
def JSON_units(request, company):
    # at the moment, company is not needed
    return JSON_response(g.UNITS) # G units!
    
def products(request, company):
    c = get_object_or_404(Company, url_name = company)
    
    # needs to be ay least guest to view products
    if not has_permission(request.user, c, 1):
        return no_permission_view(request, c, _("view products"))
    
    context = {
        'company':c, 
        'title':_("Products"),
        'site_title':g.MISC['site_title'],
        # urls for ajax calls
        'add_url':reverse('pos:create_product', args=[c.url_name]),
        # config variables 
        'can_edit':has_permission(request.user, c, 10),  # must be a seller to edit products
        'default_tax':get_value(request.user, 'pos_default_tax'),
        'currency':get_value(request.user, 'pos_currency'),
    }
    return render(request, 'pos/manage/products.html', context)

def product_to_dict(user, product):
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
    
    ret['id'] = product.id
    
    try: # only the last price from the price table
        price = Price.objects.filter(product__id=product.id).order_by('-date_updated')[0]
        price = format_number(price.unit_price)
    except:
        price = ''
        pass
    
    ret['price'] = price
    
    # all discounts in a list
    discounts = {}
    for d in product.discounts.all():
        discounts[str(d.id)] = discount_to_dict(user, d)

    ret['discounts'] = discounts
    
    # check if product's image exists
    # TODO: better image handling
    if product.image:
        ret['image'] = product.image.url
    
    # category?
    if product.category:
        ret['category'] = product.category.name
    
    if product.code:
        ret['code'] = product.code
    if product.shop_code:
        ret['shop_code'] = product.shop_code
    if product.name:
        ret['name'] = product.name
    if product.description:
        ret['description'] = product.description
    if product.private_notes:
        ret['private_notes'] = product.private_notes
    if product.unit_type:
        ret['unit_type'] = product.unit_type
        ret['unit_type_display'] = product.get_unit_type_display()
    if product.tax:
        ret['tax'] = format_number(product.tax)
    if product.stock:
        ret['stock'] = format_number(product.stock)
    
    # urls
    ret['get_url'] = reverse('pos:get_product', args=[product.company.url_name, product.id])
    ret['edit_url'] = reverse('pos:edit_product', args=[product.company.url_name, product.id])
    ret['delete_url'] = reverse('pos:delete_product', args=[product.company.url_name, product.id]) 
    
    return ret

def update_price(product, user, new_unit_price):
    """ set a new price for product:
         - if there's no price, just create new
         - if there is a price, update its date_updated to now() and create new
           (only if value is different)
         - return current price
    """
    try:
        old_price = Price.objects.get(product=product, date_updated=None)
    except Price.DoesNotExist:
        old_price = None

    if old_price:
        if old_price.unit_price == new_unit_price:
            # nothing has changed, so do nothing
            return old_price
    
        # update the old price
        old_price.date_updated = dtm.datetime.now() \
                .replace(tzinfo=pytz.timezone(get_value(user, 'pos_timezone')))
        old_price.save()
            
    # create new
    new_price = Price(created_by = user,
                      product = product,
                      unit_price = new_unit_price)
    new_price.save()
    return new_price

def get_product(request, company, product_id):
    c = get_object_or_404(Company, url_name = company)
    
    # permissions: needs to be guest to view products
    if not has_permission(request.user, c, 1):
        return error(_("You have no permission to view products"))
    
    product = get_object_or_404(Product, id = product_id, company = c)
    
    return JSON_response(product_to_dict(request.user, product))
    
def search_products(request, company):
    c = get_object_or_404(Company, url_name = company)
    
    # permissions: needs to be guest
    if not has_permission(request.user, c, 1):
        return error(_("You have no permission to view products"))
    
    # get all products from this company and filter them by entered criteria
    products = Product.objects.filter(company=c)
    
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
        products = products.filter(code__icontains = criteria.get('product_code_filter'))
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
            products = products.filter( \
                pk__in=Price.objects.filter( \
                    unit_price=d.Decimal(\
                        criteria.get('price_filter'))).order_by('-date_updated')[:1])
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
        ps.append(product_to_dict(request.user, p))

    return JSON_response(ps)

def validate_product(data, company):
    # data format (*-validation needed):
    # id
    # name*
    # price - numeric value*
    # unit type
    # discounts - list of discount ids (checked in create/edit_product)
    # image - TODO
    # category - id (checked in create/edit_product)
    # code*
    # shop code*
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
    
    try:
        data['id'] = int(data['id'])
    except:
        # this shouldn't happen
        return r(_("Wrong product id"))
    
    # name
    if not data['name']:
        return r(False, _("No name entered"))
    data['name'] = data['name'].strip()
    
    # price
    try:
        data['price'] = d.Decimal(data['price'])
    except:
        return r(False, _("Check price notation"))
        
    # unit type (probably doesn't need checking
    if not data['unit_type'] in dict(g.UNITS):
        return r(False, _("Invalid unit type"))

    # TODO: image
    
    # code: must exist and must be unique
    data['code'] = data['code'].strip()
    if not data['code']:
        return r(False, _("No code entered"))
    else:
        try:
            p = Product.objects.get(company=company, code=data['code'])
            if p.id != data['id']:
                # same ids = product is being edited, so codes can be the same
                # if ids are not the same, it's either new product or another product's code 
                return r(False,
                    _("A product with this code already exists: ") + p.name)
        except Product.DoesNotExist:
            pass # there is no product with this code, everything is ok
    
    # shop code: if exists, must be unique
    data['shop_code'] = data['shop_code'].strip()
    if data['shop_code']:
        try:
            data['shop_code'] = int(data['shop_code'])
        except:
            return r(False, _("Check shop code"))
        
        try:
            p = Product.objects.get(company=company, shop_code=data['shop_code'])
            if p.id != data['id']:
                return r(False,
                    _("A product with this shop code already exists: ") + p.name)
        except Product.DoesNotExist:
            pass # ok
    
    # description, notes - anything can be entered
    data['description'] = data['description'].strip()
    data['private_notes'] = data['private_notes'].strip()
    
    
    try:
        data['tax'] = d.Decimal(data['tax'].strip())
    except:
        return r(False, _("Check tax notation"))
    
    try:
        data['stock'] = d.Decimal(data['stock'].strip())
    except:
        return r(False, _("Check stock notation"))
    
    return {'status':True, 'data':data} 
    
def create_product(request, company):
    # create new product
    c = get_object_or_404(Company, url_name = company)
    
    # sellers can add product
    if not has_permission(request.user, c, 10):
        return JSON_error(_("You have no permission to add products"))

    data = JSON_parse(request.POST['data'])
    
    # validate data
    valid = validate_product(data, c)
    if not valid['status']:
        return JSON_error(valid['message'])
    data = valid['data']
    
    try:
        category = Category.objects.get(id=data['category'])
    except Category.DoesNotExist:
        return JSON_error(_("Category does not exist"))
    
    # update product:
    # TODO: image
    product = Product(
        company = c,
        created_by = request.user,
        category = category,
        name = data['name'],
        unit_type = data['unit_type'],
        code = data['code'],
        shop_code = data['shop_code'],
        description = data['description'],
        private_notes = data['private_notes'],
        stock = data['stock'],
        tax = data['tax'],
    )
    product.save()
    
    # add discounts
    for d in data['discounts']:
        try:
            discount = Discount.objects.get(id=int(d))
            product.discounts.add(discount)
        except Discount.DoesNotExist:
            pass
    
    # price has to be updated separately
    product.price = update_price(product, request.user, data['price'])

    return JSON_ok()

def edit_product(request, company, product_id):
    # update existing product
    c = get_object_or_404(Company, url_name = company)
    
    # sellers can edit product
    if not has_permission(request.user, c, 10):
        return JSON_error(_("You have no permission to edit products"))

    data = JSON_parse(request.POST['data'])
    
    # see if product exists in database
    try:
        product = Product.objects.get(id=product_id)
    except:
        return JSON_error(_("Product does not exist"))
    
    # validate data
    valid = validate_product(data, c)
    if not valid['status']:
        return JSON_error(valid['message'])
    data = valid['data']
    
    # update product:
    product.unit_type = data['unit_type']
    product.code = data['code']
    product.shop_code = data['shop_code']
    product.description = data['description']
    product.private_notes = data['private_notes']
    product.stock = data['stock']
    product.tax = data['tax']
    
    # update discounts: remove deleted
    discounts = product.discounts.all()
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

    # price has to be updated separately
    product.price = update_price(product, request.user, data['price'])
    
    product.save()

    return JSON_ok()

def delete_product(request, company, product_id):
    c = get_object_or_404(Company, url_name = company)
    
    # sellers can delete products
    if not has_permission(request.user, c, 10):
        return JSON_error(_("You have no permission to delete products"))
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JSON_error(_("Product does not exist"))
    
    product.delete()
    
    return JSON_ok()