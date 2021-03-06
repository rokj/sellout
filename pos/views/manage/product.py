import base64
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from common.decorators import login_required
from django.utils.translation import ugettext as _
from django.db.models import Q
from common.images import image_dimensions, import_color_image, create_file_from_image

from pos.models import Company, Category, Product, Price, Tax, Discount, ProductDiscount
from common.functions import JsonParse, JsonError, JsonOk, \
                           has_permission, no_permission_view, \
                           format_number, parse_decimal, \
                           max_field_length, error, JsonStringify
from pos.models import StockProduct
from pos.views.manage.discount import discount_to_dict, get_all_discounts
from pos.views.manage.category import get_subcategories, get_all_categories
from pos.views.manage.tax import get_default_tax, get_all_taxes

from common import globals as g
from config.functions import get_company_value

import decimal
from sorl.thumbnail import get_thumbnail
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

###############
## products ###
###############

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_JSON_units(request, company):
    return JSON_units(request, company)

@login_required
def JSON_units(request, company):
    # at the moment, company is not needed
    # also, no permission checking is required
    return JsonResponse(g.UNITS)  # G units!


def product_to_dict(user, company, product, android=False):
    # returns all relevant product's data
    ret = {}

    ret['id'] = product.id

    # purchase price
    purchase_price = product.get_purchase_price()
    if not purchase_price:
        ret['purchase_price'] = ''
    else:
        ret['purchase_price'] = format_number(user, company, purchase_price, True)

    # sale price
    price = product.get_price()

    if price is None:
        ret['price'] = ''
    else:
        ret['price'] = format_number(user, company, price, True)

    # all discounts in a list
    discounts = []
    all_discounts = product.get_discounts()
    for d in all_discounts:
        # discounts.append(d.id)
        discounts.append(discount_to_dict(user, company, d, android))
    ret['discounts'] = discounts
    if product.image:  # check if product's image exists:
        if android:
            # uf, if images are big, then what, at least we should thumnbnail-it
            with open(product.image.path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())
            ret['image'] = encoded_string
        else:
            ret['image'] = get_thumbnail(product.image, image_dimensions('product')[2]).url

    # tax: it's a not-null foreign key
    ret['tax_id'] = product.tax.id
    ret['tax'] = format_number(user, company, product.tax.amount)

    # category?
    if product.category:
        ret['category'] = product.category.name
        ret['category_id'] = product.category.id
    else:
        ret['category'] = g.NO_CATEGORY_NAME
        ret['category_id'] = -1

    ret['code'] = product.code
    ret['shortcut'] = product.shortcut
    ret['name'] = product.name
    ret['description'] = product.description
    ret['private_notes'] = product.private_notes
    ret['unit_type'] = product.unit_type
    ret['unit_type_display'] = product.get_unit_type_display()
    # stock: it cannot be 'undefined'
    # ret['stock'] = format_number(user, company, product.stock)
    ret['color'] = product.color
    ret['favorite'] = product.favorite

    if hasattr(product, 'stock_products'):
        stock_products = []

        for sp in product.stock_products:
            stock_product = {}
            stock_product['stock_name'] = sp.stock.name
            stock_product['deduction'] = sp.deduction
            stock_product['left_stock'] = sp.stock.left_stock
            stock_product['stock_unit_type'] = sp.stock.unit_type
            stock_products.append(stock_product)

        ret['stock_products'] = stock_products

    return ret


@login_required
def products(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # needs to be at least guest to view products
    if not has_permission(request.user, c, 'product', 'view'):
        return no_permission_view(request, c, _("You have no permission to view products."))

    # if there are no taxes defined, don't show anything
    if Tax.objects.filter(company=c).count() == 0:
        return error(request, c, _("There are no taxes defined. Please go to tax management and define them."))

    # if there are no categories defined, throw an error
    # [this is no longer required since category on product isn't required either]
    # if Category.objects.filter(company=c).count() == 0:
    #    return error(request, c, _("There are no categories defined, please go to category management to define them."))

    # list of categories: one additional 'category': no category set, that is 'None'
    categories = get_all_categories(c, json=True)
    categories.append({
        'id': -1,
        'name': g.NO_CATEGORY_NAME,
        'description': "",
        'parent_id': None,

        'color': g.CATEGORY_COLORS[0],  # the default
        'breadcrumbs': g.NO_CATEGORY_NAME,
        'path': g.NO_CATEGORY_NAME,
        'level': 0
    })

    # fields that need to be limited in length:
    lengths = {
        'code': max_field_length(Product, 'code'),
        'price': g.DECIMAL['currency_digits'] + 1,
        'purchase_price': g.DECIMAL['currency_digits'] + 1,
        'shortcut': max_field_length(Product, 'shortcut'),
        'stock': g.DECIMAL['quantity_digits'],
        'name': max_field_length(Product, 'name'),
        'tax': g.DECIMAL['percentage_decimal_places'] + 4,  # up to '100.' + 'decimal_digits'
    }

    context = {
        'company': c,
        'title': _("Products"),
        'site_title': g.MISC['site_title'],
        # lists
        'taxes': JsonStringify(get_all_taxes(request.user, c)),
        'categories': JsonStringify(categories),
        'units': JsonStringify(g.UNITS),
        'discounts': JsonStringify(get_all_discounts(request.user, c)),
        # urls for ajax calls
        'add_url': reverse('pos:create_product', args=[c.url_name]),
        # config variables
        'can_edit': has_permission(request.user, c, 'product', 'edit'),
        'currency': get_company_value(request.user, c, 'pos_currency'),
        # images
        'image_dimensions': g.IMAGE_DIMENSIONS['product'],
        'image_upload_formats': g.MISC['image_upload_formats'], # what can be uploaded
        'max_upload_size': round(g.MISC['max_upload_image_size']/2**20, 2), # show in megabytes
        'max_upload_size_bytes': g.MISC['max_upload_image_size'], # bytes for javascript
        # html fields
        'field_lengths': lengths,
        'separator': get_company_value(request.user, c, 'pos_decimal_separator'),
        # numbers etc
        'default_tax_id': get_default_tax(request.user, c)['id'],
        'decimal_places': get_company_value(request.user, c, 'pos_decimal_places')*2,  # ACHTUNG: rounding comes at the end
    }

    return render(request, 'pos/manage/products.html', context)


@login_required
def get_product(request, company):
    try:
        c = Company.objects.get(url_name=company)
        return get_product_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))
    
    # permissions


def get_product_(request, c):
    if not has_permission(request.user, c, 'product', 'view'):
        return JsonError(_("You have no permission to view products"))

    try:
        product_id = int(request.GET.get('product_id'))
    except (ValueError, TypeError):
        return JsonError(_("No product specified"))

    if product_id == -1:
        return JsonError(_("No product specified"))

    product = Product.objects.get(company=c, id=product_id)

    return JsonResponse(product_to_dict(request.user, c, product))


@login_required
def search_products(request, company):
    try:
        c = Company.objects.get(url_name=company)
        return search_products_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def search_products_(request, c, android=False):
    # permissions: needs to be guest
    if not has_permission(request.user, c, 'product', 'view'):
        return JsonError(_("You have no permission to view products"))
    
    # get all products from this company and filter them by entered criteria
    products = Product.objects.filter(company=c)
    
    criteria = JsonParse(request.POST.get('data'))
    
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
        products = products.filter(code__icontains=criteria.get('product_code_filter'))
    else:
        filter_by_product_code = False
    
    # shortcut_filter
    if criteria.get('shortcut_filter'):
        filter_by_shortcut = True
        products = products.filter(shortcut__icontains=criteria.get('shortcut_filter'))
    else:
        filter_by_shortcut = False
    
    # notes_filter
    if criteria.get('notes_filter'):
        filter_by_notes = True
        products = products.filter(private_notes__icontains=criteria.get('notes_filter'))
    else:
        filter_by_notes = False
        
    # description_filter
    if criteria.get('description_filter'):
        filter_by_description = True
        products = products.filter(description__icontains=criteria.get('description_filter'))
    else:
        filter_by_description = False
        
    # category_filter: filter by category or only products with no category, or don't filter at all
    if criteria.get('category_filter'):
        filter_by_category = True
        category_id = int(criteria.get('category_filter'))

        if category_id == -1:
            products = products.filter(category=None)
        else:
            products = products.filter(category__id__in=get_subcategories(category_id, data=[]))
    else:
        filter_by_category = False
        
    # tax_filter
    if criteria.get('tax_filter') and criteria.get('tax_filter').isdigit():
        #filter_by_tax = True
        products = products.filter(tax_id=int(criteria.get('tax_filter')))
    else:
        pass
        #filter_by_tax = False
    
    # price_filter
    if criteria.get('price_filter'):
        try:
            products = products.filter(
                pk__in=Price.objects.filter(
                    unit_price=decimal.Decimal(
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
        products = products.filter(discounts__code=criteria.get('discount_filter'))
    else:
        pass
        #filter_by_discount = False

    # general filter: search all fields that have not been searched yet 
    general_filter = criteria.get('general_filter')
    #g_products = Product.objects.none()
    if general_filter:
        general_filter = general_filter.split(' ')
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

    products = products.distinct().order_by('name')[:g.SEARCH_RESULTS['products']]

    # return serialized products
    ps = []
    for p in products:
        p.stock_products = StockProduct.objects.filter(product=p)
        ps.append(product_to_dict(request.user, c, p, android=android))

    return JsonResponse(ps, safe=False)


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
    # shortcut*
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
    except (ValueError, TypeError):
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
    
    # category: leave null if it doesn't exist
    if not data.get('category_id'):
        return r(False, _("No category assigned"))
    else:
        try:
            category_id = int(data['category_id'])

            if category_id == -1:
                data['category_id'] = None
                data['category'] = None
            else:
                data['category_id'] = category_id
                data['category'] = Category.objects.get(id=data['category_id'], company=company)
        except Category.DoesNotExist:
            return r(False, _("Selected category does not exist"))

    # price
    if len(data['price']) > g.DECIMAL['currency_digits']+1:
        return r(False, _("Price too long"))
    
    ret = parse_decimal(user, company, data['price'], g.DECIMAL['currency_digits'])
    if not ret['success']:
        return r(False, _("Check price notation"))
    data['price'] = ret['number']
    
    # purchase price
    if 'purchase_price' in data:
        if len(data['purchase_price']) > g.DECIMAL['currency_digits']+1:
            return r(False, _("Purchase price too long"))
    
        if len(data['purchase_price']) > 1:  # purchase price is not mandatory, so don't whine if it's not entered
            ret = parse_decimal(user, company, data['purchase_price'], g.DECIMAL['currency_digits'])
            if not ret['success']:
                return r(False, _("Check purchase price notation"))
            data['purchase_price'] = ret['number']

    # unit type (probably doesn't need checking
    if not (data['unit_type'] in g.UNIT_CODES):
        return r(False, _("Invalid unit type"))

    # image:
    if data['change_image'] == True:
        if 'image' in data and data['image']:  # a new image has been uploaded
            data['image'] = import_color_image(data['image'], g.IMAGE_DIMENSIONS['product'], 'fill')
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
    
    # shortcut: if exists, must be unique
    data['shortcut'] = data['shortcut'].strip()
    if data['shortcut']:
        if len(data['shortcut']) > max_field_length(Product, 'shortcut'):
            return r(False, _("Shortcut too long"))
        
        try:
            p = Product.objects.get(company=company, shortcut=data['shortcut'])
            if p.id != data['id']:
                return r(False,
                    _("A product with this shortcut already exists: ") + p.name)
        except Product.DoesNotExist:
            pass  # ok
    
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
    # if len(data['stock']) > g.DECIMAL['quantity_digits']:
    #    return r(False, _("Stock number too big"))
    
    # ret = parse_decimal(user, company, data['stock'],
    #    g.DECIMAL['quantity_digits']-g.DECIMAL['quantity_decimal_places']-1)
    #if not ret['success']:
    #    return r(False, _("Check stock notation"))
    #else:
    #    data['stock'] = ret['number']
        # it cannot be negative
        # EDIT: stock can be negative
        #if data['stock'] < decimal.Decimal('0'):
        #    return r(False, _("Stock cannot be negative"))
        
    return {'status': True, 'data': data}


@login_required
def create_product(request, company):
    # create new product
    try:
        c = Company.objects.get(url_name=company)
        return create_product_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def create_product_(request, c, android=False):
    if not has_permission(request.user, c, 'product', 'edit'):
        return JsonError(_("You have no permission to add products"))

    data = JsonParse(request.POST['data'])
    
    # validate data
    valid = validate_product(request.user, c, data)
    if not valid['status']:
        return JsonError(valid['message'])
    data = valid['data']
    
    # save product:
    product = Product(
        company=c,
        created_by=request.user,
        category=data.get('category'),
        name=data.get('name'),
        code=data.get('code'),
        shortcut=data.get('shortcut'),
        description=data.get('description'),
        private_notes=data.get('private_notes'),
    #     stock=data.get('stock'),
        tax=data.get('tax'),
        unit_type=data.get('unit_type')
    )
    product.save()
    
    # update discounts
    product.update_discounts(request.user, data['discount_ids'])
    
    # prices have to be updated separately
    price = product.update_price(Price, request.user, data['price']) # purchase price
    if not price:
        product.delete()
        return JsonError(_("Error while setting purchase price"))


    # if data.get('purchase_price'):
    #     price = product.update_price(PurchasePrice, request.user, data['purchase_price'])
    #     if not price:
    #         product.delete()
    #         return JsonError(_("Error while setting sell price"))
    
    # add image, if it's there
    if data['change_image']:
        if 'image' in data:
            f = create_file_from_image(data['image'])
            product.image = f['file']
            product.save()
    
    return JsonOk(extra=product_to_dict(request.user, c, product, android))


@login_required
def edit_product(request, company):
    # update existing product
    try:
        c = Company.objects.get(url_name=company)
        return edit_product_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def edit_product_(request, c, android=False):
    # sellers can edit product
    if not has_permission(request.user, c, 'product', 'edit'):
        return JsonError(_("You have no permission to edit products"))

    data = JsonParse(request.POST['data'])

    # see if product exists in database
    product_id = data['id']
    try:
        product = Product.objects.get(company=c, id=product_id)
    except:
        return JsonError(_("Product does not exist"))
    
    # validate data
    valid = validate_product(request.user, c, data)
    if not valid['status']:
        return JsonError(valid['message'])
    data = valid['data']
    
    # update product:
    product.name = data.get('name')
    product.category = data.get('category')
    product.unit_type = data.get('unit_type')
    product.code = data.get('code')
    product.shortcut = data.get('shortcut')
    product.description = data.get('description')
    product.private_notes = data.get('private_notes')
    # product.stock = data.get('stock')
    product.tax = data.get('tax')
    
    # update discounts
    product.update_discounts(request.user, data['discount_ids'])
    
    # image
    if data['change_image'] == True:
        if data.get('image'):  # new image is uploaded
            # create a file from the base64 data and save it to product.image
            if product.image:
                product.image.delete()
            # save a new image (conversion is done in validate_product)
            f = create_file_from_image(data['image'])
            product.image = f['file']
        else:  # delete the old image
            product.image.delete()
    
    # category
    if data['category']:
        product.category = data['category']

    # price has to be updated separately
    product.price = product.update_price(Price, request.user, data['price'])
    # if data.get('purchase_price'):
    #     product.price = product.update_price(PurchasePrice, request.user, data['purchase_price'])

    product.updated_by = request.user
    product.save()

    return JsonOk(extra=product_to_dict(request.user, c, product, android))


@login_required
def delete_product(request, company):
    try:
        c = Company.objects.get(url_name=company)
        return delete_product_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def delete_product_(request, c):
    # sellers can delete products
    if not has_permission(request.user, c, 'product', 'edit'):
        return JsonError(_("You have no permission to delete products"))

    data = JsonParse(request.POST['data'])
    product_id = data['id']

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonError(_("Product does not exist"))
    
    product.delete()
    
    return JsonOk(extra=product_to_dict(request.user, c, product))


def get_all_products(user, company):
    products = Product.objects.filter(company=company)

    # maybe we'll need this in the future
    # for p in products:
    #   p.stock_products = StockProduct.objects.filter(product=p)

    r = []
    for p in products:
        r.append(product_to_dict(user, company, p))

    return r


@login_required
def toggle_favorite(request, company):
    # company
    try:
        c = Company.objects.get(url_name=company)
        return toggle_favorite_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def toggle_favorite_(request, c):
    # permissions
    if not has_permission(request.user, c, 'product', 'edit'):
        return JsonError(_("You have no permission to edit products"))

    # data in POST request: product
    try:
        product_id = int(JsonParse(request.POST.get('data')).get('product_id'))
    except ValueError:
        return JsonError(_("Invalid data"))

    # get the product
    try:
        product = Product.objects.get(id=product_id, company=c)
    except Product.DoesNotExist:
        return JsonError(_("Product does not exist"))

    # if product is already a favorite, remove it
    product.favorite = not product.favorite
    product.save()

    return JsonResponse({'status': 'ok', 'favorite': product.favorite})


@login_required
def mass_edit(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # there must be stuff in request.POST
    data = JsonParse(request.POST.get('data'))

    if not data:
        return JsonError(_("No data in request"))

    # get product ids from data
    if len(data.get('products')) == 0:
        return JsonError(_("No products selected"))

    products = Product.objects.filter(company=c, id__in=data.get('products'))
    action = data.get('action')

    # decide what to do for each action
    if action == 'set-tax':
        # get the tax with given id and put it on all products
        try:
            tax = Tax.objects.get(company=c, id=data.get('id'))
        except (Tax.DoesNotExist, ValueError, TypeError):
            return JsonError(_("Tax does not exist"))

        for p in products:
            p.tax = tax
            p.save()

        return JsonOk()

    elif action == 'add-discount':
        # go through each product and add a discount
        try:
            discount = Discount.objects.get(company=c, id=data.get('id'))
        except (Discount.DoesNotExist, ValueError, TypeError):
            return JsonError(_("Discount does not exist or is not valid"))

        # add this discount to all products in list
        for p in products:
            p.add_discount(request.user, discount)

        return JsonOk()

    elif action == 'remove-discount':
        try:
            discount = Discount.objects.get(company=c, id=data.get('id'))
        except (Discount.DoesNotExist, ValueError, TypeError):
            return JsonError(_("Discount does not exist or is not valid"))

        # remove this discount from all products in list
        for p in products:
            p.remove_discount(discount)

        return JsonOk()

    elif action == 'clear-discounts':
        # there is no discounts, just remove all discounts from all products in the list
        for p in products:
            ProductDiscount.objects.filter(product=p).delete()

        return JsonOk()

    elif action == 'delete':
        # delete all products in the list
        for p in products:
            p.delete()

        return JsonOk()

    else:
        return JsonError(_("Unsupported mass edit action"))


