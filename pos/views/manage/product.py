from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db.models import Q

from pos.models import Company, Category, Discount, Product, Price, Tax
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

@login_required
def web_JSON_units(request, company):
    return JSON_units(request, company)


def JSON_units(request, company):
    # at the moment, company is not needed
    # also, no permission checking is required
    return JSON_response(g.UNITS) # G units!

@login_required
def products(request, company):
    c = get_object_or_404(Company, url_name = company)
    
    # needs to be at least guest to view products
    if not has_permission(request.user, c, 'product', 'list'):
        return no_permission_view(request, c, _("view products"))
    
    # fields that need to be limited in length:
    lengths = {
        'code':max_field_length(Product, 'code'),
        'price':g.DECIMAL['currency_digits'] + 1,
        'shortcut':max_field_length(Product, 'shortcut'),
        'stock':g.DECIMAL['quantity_digits'],
        'name':max_field_length(Product, 'name'),
        'tax':g.DECIMAL['percentage_decimal_places'] + 4, # up to '100.' + 'decimal_digits'
    }
    
    context = {
        'company':c, 
        'title':_("Products"),
        'site_title':g.MISC['site_title'],
        # urls for ajax calls
        'add_url':reverse('pos:web_create_product', args=[c.url_name]),
        # config variables 
        'can_edit':has_permission(request.user, c, 'product', 'edit'),
        'currency':get_value(request.user, 'pos_currency'),
        # images
        'image_dimensions':g.IMAGE_DIMENSIONS['product'],
        'image_upload_formats':g.MISC['image_upload_formats'], # what can be uploaded
        'max_upload_size':round(g.MISC['max_upload_image_size']/2**20, 2), # show in megabytes
        'max_upload_size_bytes':g.MISC['max_upload_image_size'], # bytes for javascript
        # html fields
        'field_lengths':lengths,
        'separator':get_value(request.user, 'pos_decimal_separator'),
        # numbers etc
        'default_tax_id':get_default_tax(request.user, c)['id'],
        'min_decimal_places':2,
        'max_decimal_places':g.DECIMAL['currency_decimal_places'],
    }
    return render(request, 'pos/manage/products.html', context)

def product_to_dict(user, product):
    # returns all relevant product's data:
    # id
    # price - numeric value
    # unit type
    # discounts - dictionary or all discounts for this product 
    #    (see discounts.discount_to_dict for details)
    # image
    # category - name
    # category - id
    # code
    # shop code
    # description
    # private notes
    # tax
    # tax - id
    # stock
    # edit url
    ret = {}
    
    ret['id'] = product.id
    
    try: # only the last price from the price table
        price = Price.objects.filter(product__id=product.id).order_by('-datetime_updated')[0]
        price = format_number(user, price.unit_price)
    except:
        price = ''
        pass
    
    ret['price'] = price
    
    # all discounts in a list
    discounts = []
    for d in product.discounts.all().order_by('topping_relationship__order_to_add_topping'):
        print d
        discounts.append(discount_to_dict(user, d))
        
    ret['discounts'] = discounts
    
    if product.image: # check if product's image exists
        # get the thumbnail
        try:
            ret['image'] = get_thumbnail(product.image, image_dimensions('product')[2]).url
        except:
            pass
    
    # tax: it's a not-null foreign key
    ret['tax_id'] = product.tax.id
    ret['tax'] = format_number(user, product.tax.amount)
            
    # category?
    if product.category:
        ret['category'] = product.category.name
    
    if product.category:
        ret['category_id'] = product.category.id
    
    if product.code:
        ret['code'] = product.code
    if product.shortcut:
        ret['shortcut'] = product.shortcut
    if product.name:
        ret['name'] = product.name
    if product.description:
        ret['description'] = product.description
    if product.private_notes:
        ret['private_notes'] = product.private_notes
    if product.unit_type:
        ret['unit_type'] = product.unit_type
        ret['unit_type_display'] = product.get_unit_type_display()
    if product.stock:
        ret['stock'] = format_number(user, product.stock)
    
    # urls
    ret['get_url'] = reverse('pos:get_product', args=[product.company.url_name, product.id])
    ret['edit_url'] = reverse('pos:edit_product', args=[product.company.url_name, product.id])
    ret['delete_url'] = reverse('pos:delete_product', args=[product.company.url_name, product.id]) 
    
    return ret

def update_price(product, user, new_unit_price):
    """ set a new price for product:
         - if there's no price, just create new
         - if there is a price, update its datetime_updated to now() and create new
           (only if value is different)
         - return current price
    """
    try:
        old_price = Price.objects.get(product=product, datetime_updated=None)
    except Price.DoesNotExist:
        old_price = None

    if old_price:
        if old_price.unit_price == new_unit_price:
            # nothing has changed, so do nothing
            return old_price
    
        # update the old price (datetime_updated will be set)
        old_price.save()
            
    # create new
    new_price = Price(created_by = user,
                      product = product,
                      unit_price = new_unit_price)
    new_price.save()
    
    return new_price

@login_required
def web_get_product(request, company, product_id):
    return get_product(request, company, product_id)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_product(request, company, product_id):
    return get_product(request, company, product_id)

def get_product(request, company, product_id):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # permissions: needs to be guest to view products
    if not has_permission(request.user, c, 'product', 'list'):
        return JSON_error(_("You have no permission to view products"))
    
    product = get_object_or_404(Product, id = product_id, company = c)
    
    return JSON_response(product_to_dict(request.user, product))

@login_required
def web_search_products(request, company):
    return search_products(request, company)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_search_products(request, company):
    return search_products(request, company)

def search_products(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # permissions: needs to be guest
    if not has_permission(request.user, c, 'product', 'list'):
        return JSON_error(_("You have no permission to view products"))
    
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
    
    # shortcut_filter
    if criteria.get('shortcut_filter'):
        filter_by_shortcut = True
        products = products.filter(shortcut__icontains = criteria.get('shortcut_filter'))
    else:
        filter_by_shortcut = False
    
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
        
    # category_filter
    if criteria.get('category_filter'):
        filter_by_category = True
        products = products.filter(category__id__in=get_subcategories(int(criteria.get('category_filter')), data=[]))
    else:
        filter_by_category = False
        
    # tax_filter
    if criteria.get('tax_filter'):
        #filter_by_tax = True
        products = products.filter(tax = decimal.Decimal(criteria.get('tax_filter')))
    else:
        pass
        #filter_by_tax = False
    
    # price_filter
    if criteria.get('price_filter'):
        try:
            products = products.filter( \
                pk__in=Price.objects.filter( \
                    unit_price=decimal.Decimal(\
                        criteria.get('price_filter'))).order_by('-datetime_updated')[:1])
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
        
        # search categories, product_code, shortcut, name, description, notes,
        # but only if it wasn't entered in the "advanced" filter
        # assemble the Q() filter
        f = Q()
        if not filter_by_name:
            f = f | Q(name__icontains=w)
        if not filter_by_product_code:
            f = f | Q(code__icontains=w)
        if not filter_by_shortcut:
            f = f | Q(shortcut__icontains=w)
        if not filter_by_notes:
            f = f | Q(private_notes__icontains=w)
        if not filter_by_description:
            f = f | Q(description__icontains=w)
        if not filter_by_category:
            # get the categories that match this string and search by their subcategories also
            tmpcat = Category.objects.filter(name__icontains=w)
            for t in tmpcat:
                f = f | Q(category__id__in=get_subcategories(t.id, data=[]))

        if f:
            products = products.filter(f)
        # omit search by tax, price, discount

    products = products.distinct().order_by('name')
    
    # return serialized products
    ps = []
    for p in products:
        ps.append(product_to_dict(request.user, p))

    return JSON_response(ps)

def validate_product(user, company, data):
    # data format (*-validation needed):
    # id
    # name*
    # price - numeric value*
    # unit type
    # discounts - list of discount ids (checked in create/edit_product)
    # image
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
        return r(False, _("Wrong product id"))
    
    
    if data['id'] != -1:
        # check if product belongs to this company and if he has the required permissions
        try:
            p = Product.objects.get(id=data['id'], company=company)
        except Product.DoesNotExist:
            return r(False, _("Cannot edit product: it does not exist"))
        
        if p.company != company or not has_permission(user, company, 'product', 'edit'):
            return r(False, _("You have no permission to edit this product"))
    
    # name
    if not data['name']:
        return r(False, _("No name entered"))
    elif len(data['name']) > max_field_length(Product, 'name'):
        return r(False, _("Name too long"))
    else:
        if data['id'] == -1: # when adding new products:
            # check if a product with that name exists
            p = Product.objects.filter(company=company,name=data['name'])
            if p.count() > 0:
                return r(False,
                    _("There is already a product with that name") +  \
                    " (" + _("code") + ": " + p[0].code + ")")
    data['name'] = data['name'].strip()
    
    # price
    if len(data['price']) > g.DECIMAL['currency_digits']+1:
        return r(False, _("Price too long"))
    
    ret = parse_decimal(user, data['price'], g.DECIMAL['currency_digits'])
    if not ret['success']:
        return r(False, _("Check price notation"))
    data['price'] = ret['number']
    
        
    # unit type (probably doesn't need checking
    if not data['unit_type'] in dict(g.UNITS):
        return r(False, _("Invalid unit type"))

    # image:
    if data['change_image'] == True:
        if 'image' in data: # new image has been uploaded
            data['image'] = image_from_base64(data['image'])
            if not data['image']:
                # something has gone wrong during conversion
                return r(False, _("Image upload failed"))
        else:
            # image will be deleted in view
            pass
    else:
        # no change regarding images
        data['image'] = None
            
    # code: must exist and must be unique
    data['code'] = data['code'].strip()
    if not data['code']:
        return r(False, _("No code entered"))
    else:
        if len(data['code']) > max_field_length(Product, 'code'):
            return r(False, _("Code too long"))
        
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
    data['shortcut'] = data['shortcut'].strip()
    if data['shortcut']:
        if len(data['shortcut']) > max_field_length(Product, 'shortcut'):
            return r(False, _("Shop code too long"))
        
        try:
            p = Product.objects.get(company=company, shortcut=data['shortcut'])
            if p.id != data['id']:
                return r(False,
                    _("A product with this shop code already exists: ") + p.name)
        except Product.DoesNotExist:
            pass # ok
    
    # description, notes - anything can be entered
    data['description'] = data['description'].strip()
    data['private_notes'] = data['private_notes'].strip()
    
    # tax: id should be among tax rates for this company
    try:
        tax = Tax.objects.get(id=int(data['tax_id']))
    except:
        return r(False, _("Invalid tax rate"))

    del data['tax_id']
    data['tax'] = tax
    
    # stock
    if len(data['stock']) > g.DECIMAL['quantity_digits']:
        return r(False, _("Stock number too big"))
    
    ret = parse_decimal(user, data['stock'],
        g.DECIMAL['quantity_digits']-g.DECIMAL['quantity_decimal_places']-1)
    if not ret['success']:
        return r(False, _("Check stock notation"))
    else:
        data['stock'] = ret['number']
        
    return {'status':True, 'data':data} 

@login_required
def web_create_product(request, company):
    return create_product(request, company)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_create_product(request, company):
    return create_product(request, company)

def create_product(request, company):
    # create new product
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # sellers can add product
    if not has_permission(request.user, c, 'product', 'edit'):
        return JSON_error(_("You have no permission to add products"))

    data = JSON_parse(request.POST['data'])
    
    # validate data
    valid = validate_product(request.user, c, data)
    if not valid['status']:
        return JSON_error(valid['message'])
    data = valid['data']
    
    
    try:
        category = Category.objects.get(id=data['category'])
    except Category.DoesNotExist:
        return JSON_error(_("Category does not exist"))
    
    # save product:
    product = Product(
        company = c,
        created_by = request.user,
        category = category,
        name = data['name'],
        unit_type = data['unit_type'],
        code = data['code'],
        shortcut = data['shortcut'],
        description = data['description'],
        private_notes = data['private_notes'],
        stock = data['stock'],
        tax = data['tax'],
    )
    product.save()
    
    # add discounts
    if data.get('discounts'):
        for d in data['discounts']:
            try:
                discount = Discount.objects.get(id=int(d))
                product.discounts.add(discount)
            except Discount.DoesNotExist:
                pass
    
    # price has to be updated separately
    product.price = update_price(product, request.user, data['price'])
    
    # add image, if it's there
    if data['change_image']:
        if 'image' in data:
            product.image = data['image']
            product.save()
    
    return JSON_ok()

@login_required
def web_edit_product(request, company, product_id):
    return edit_product(request, company, product_id)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_product(request, company, product_id):
    return edit_product(request, company, product_id)

def edit_product(request, company, product_id):
    # update existing product
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # sellers can edit product
    if not has_permission(request.user, c, 'product', 'edit'):
        return JSON_error(_("You have no permission to edit products"))

    data = JSON_parse(request.POST['data'])

    # see if product exists in database
    try:
        product = Product.objects.get(id=product_id)
    except:
        return JSON_error(_("Product does not exist"))
    
    # validate data
    valid = validate_product(request.user, c, data)
    if not valid['status']:
        return JSON_error(valid['message'])
    data = valid['data']
    
    # update product:
    product.name = data['name']
    product.unit_type = data['unit_type']
    product.code = data['code']
    product.shortcut = data['shortcut']
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
    if data.get('discounts'):
        for d in data['discounts']:
            try:
                discount = Discount.objects.get(id=int(d))
                product.discounts.add(discount)
            except Discount.DoesNotExist:
                pass

    # image
    if data['change_image'] == True:
        if data['image']: # new image is uploaded
            # create a file from the base64 data and save it to product.image
            if product.image:
                product.image.delete()
            # save a new image
            product.image = data['image'] # conversion from base64 is done in validate_product
        else: # delete the old image
            product.image.delete()
    
    # category
    try:
        category = Category.objects.get(id=data['category'])
        product.category = category
    except Category.DoesNotExist:
        pass # do not change product's category

    # price has to be updated separately
    product.price = update_price(product, request.user, data['price'])
    product.updated_by = request.user
    product.save()

    return JSON_ok()

@login_required
def delete_product(request, company, product_id):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # sellers can delete products
    if not has_permission(request.user, c, 'product', 'edit'):
        return JSON_error(_("You have no permission to delete products"))
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JSON_error(_("Product does not exist"))
    
    product.delete()
    
    return JSON_ok()
