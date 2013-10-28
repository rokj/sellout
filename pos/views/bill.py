from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pos.models import Company, Bill, BillItem, Price, Product
from pos.views.manage import get_all_categories_structured
from pos.views.manage.product import get_product_discounts
from pos.views.util import has_permission, no_permission_view, JSON_response, JSON_ok, JSON_parse, JSON_error, \
                           format_number, parse_decimal, format_date, format_time
from config.functions import get_value, set_value
import common.globals as g

import json
from pytz import timezone
from datetime import datetime as dtm
from decimal import Decimal

def bill_item_to_dict(user, item):
    i = {}
    
    i['id'] = item.id
    
    # values from product
    i['product_id'] = item.product_id
    i['code'] = item.code
    i['shortcut'] = item.shortcut
    i['name'] = item.name
    i['description'] = item.description
    i['private_notes'] = item.private_notes
    i['unit_type'] = item.unit_type
    i['unit_amount'] = format_number(user, item.unit_amount)
    i['stock'] = format_number(user, item.stock)
    # values from bill item
    i['bill_id'] = item.bill.id
    i['quantity'] = format_number(user, item.quantity)
    i['base_price'] = format_number(user, item.base_price)
    i['tax_percent'] = format_number(user, item.tax_percent)
    i['tax_absolute'] = format_number(user, item.tax_absolute)
    i['discount_absolute'] = format_number(user, item.discount_absolute)
    i['single_total'] = format_number(user, item.single_total)
    i['total'] = format_number(user, item.total)
    i['bill_notes'] = item.bill_notes

    return i

def bill_to_dict(user, bill):
    # fields in bill:
    # company
    # type
    # recipient_contact > FK contact
    # note
    # sub_total |
    # discount  | decimal fields, with everything calculated
    # tax       |
    # timestamp
    # status > choices in g.BILL_STATUS
    b = {}
    b['id'] = bill.id
    b['till'] = bill.till
    b['type'] = bill.type
    b['recipient_contact'] = bill.recipient_contact
    b['note'] = bill.note
    b['sub_total'] = format_number(user, bill.sub_total)
    b['discount'] = format_number(user, bill.discount)
    b['tax'] = format_number(user, bill.tax)
    b['total'] = format_number(user, bill.total)
    b['timestamp'] = format_date(user, bill.timestamp) + " " + format_time(user, bill.timestamp)
    b['due_date'] = format_date(user, bill.due_date)
    b['status'] = bill.status
    
    # items:
    items = BillItem.objects.filter(bill=bill)
    i = []
    for item in items:
        i.append(bill_item_to_dict(user, item))
        
    b['items'] = i
    
    return b

def new_bill(user, company):
    # creates an 'empty' bill in database
    # with active status
    b = Bill(
        company = company,
        user = user, # this can change
        created_by = user, # this will never change
        type = "Normal",
        timestamp = dtm.now().replace(tzinfo=timezone(get_value(user, 'pos_timezone'))),
        status = "Active"
    )
    b.save()
    
    bdict = bill_to_dict(user, b)
    
    # this is a new bill, the terminal ought to know this
    bdict['new'] = True # (this item will be deleted (ignored) on next save)

    return bdict

#########
# views #
#########
@login_required
def get_active_bill(request, company):
    """ returns the last edited (active) bill if any, or an empty one """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # check permissions
    if not has_permission(request.user, c, 'bill', 'list'):
        return JSON_error(_("You have no permission to view bills"))
    
    try:
        bill = Bill.objects.get(company=c, user=request.user, status="Active")
    except Bill.DoesNotExist:
        # if there's no active bill, start a new one
        return JSON_response(new_bill(request.user, c))
    except Bill.MultipleObjectsReturned:
        # two active bills (that shouldn't happen at all)
        return JSON_error(_("Multiple active bills found"))
        
    # serialize the fetched bill and return it
    return JSON_response(bill_to_dict(request.user, bill))

@login_required
def edit_bill_item(request, company):
    """ add an item to bill:
         - received data: {'bill':bill_id, 'product_id':<id>, 'qty':<qty>, 'notes':<notes>}
         - calculate all item's fields (tax, discount, total, ...)
         - add to bill object
         - return item_to_dict
    """
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
        
    # permissions
    if not has_permission(request.user, c, 'bill', 'edit'):
        return JSON_error(_("You have no permission to edit bills"))
    
    # data
    try:
        data = JSON_parse(request.POST.get('data'))
    except:
        return JSON_error(_("No data in POST"))
    
    # get bill
    if not data.get('bill_id'):
        return JSON_error(_("No bill specified"))
        
    try:
        bill = Bill.objects.get(company=c, id=int(data.get('bill_id')))
    except Bill.DoesNotExist:
        return JSON_error(_("This bill does not exist"))
    
    # get product
    try:
        product = Product.objects.get(company=c, id=int(data.get('product_id')))
    except Product.DoesNotExist:
        return JSON_error(_("Product with this id does not exist"))

    # parse quantity    
    r = parse_decimal(request.user, data.get('quantity'), g.DECIMAL['quantity_digits'])
    if not r['success']:
        return JSON_error(_("Invalid quantity value"))
    else:
        if r['number'] <= Decimal('0'):
            return JSON_error(_("Cannot add an item with zero or negative quantity"))
    quantity = r['number']
    
    # check if there's enough items left in stock (must be at least zero =D)
    if product.stock < quantity:
        print 'wtf'
        return JSON_error(_("Cannot sell more items than there are in stock"))
            
    # calculate and set all stuff for this new item:
    # bill (already checked)
    # quantity (already_checked)
    try:
        base_price = Price.objects.filter(product=product).order_by('-datetime_updated')[0].unit_price
    except Price.DoesNotExist:
        return JSON_error(_("Price for this product is not defined"))
    
    # tax:
    tax = product.tax.amount/Decimal('100') # percent!
    discounts = get_product_discounts(product)
    def abs_discounts_val(p, ds):
        """ from price p subtract all discounts in list d and return result """
        dabs = Decimal('0')
        for d in ds:
            d = d.discount
            # if discount is absolute, just subtract the price from p
            if d.type == "Absolute":
                dabs = dabs + d.amount
            else:
                dabs = dabs + p*d.amount/Decimal('100') # percent!
                
        return dabs
        
    # calculate discounts and tax: equation depends on configuration (first tax or first discounts)
    # for quantity = 1, then multiply
    if get_value(request.user, 'pos_discount_calculation') == "Tax first":
        # first add tax to base price, then subtract discounts
        tax_absolute = base_price * tax   # absolute tax value
        price = base_price + tax_absolute # price with tax
        discount_absolute = abs_discounts_val(price, discounts) # absolute discount value
        single_total = price - discount_absolute # price with discounts subtracted
    else:
        # first subtract discounts from base price, then add tax
        discount_absolute = abs_discounts_val(price, discounts)
        price = base_price - discount_absolute
        tax_absolute = price*tax
        single_total = price + tax_absolute
    
    total = single_total * quantity    
    
    # what's in 'price' var is not relevant and should not be used
    del price
    
    # notes, if any    
    bill_notes = data.get('notes')

    # TODO: subtract quantity from stock (if there's enough left)

    # create a bill item and save it to database, then return JSON with its data
    item = BillItem(
        created_by = request.user,
        # copy ProductAbstract's values:
        code = product.code,
        shortcut = product.shortcut,
        name = product.name,
        description = product.description,
        private_notes = product.private_notes,
        unit_type = product.get_unit_type_display(), # ! display, not the 'code'
        unit_amount = product.unit_amount,
        stock = product.stock,
        # billItem's fields        
        bill = bill,
        product_id = product.id,
        quantity = quantity,
        base_price = base_price,
        tax_percent = product.tax.amount,
        tax_absolute = tax_absolute,
        discount_absolute = discount_absolute,
        single_total = single_total,
        total = total,
        bill_notes = bill_notes
    )
    item.save()
    
    # return the item in JSON
    return JSON_response(bill_item_to_dict(request.user, item))
    
@login_required
def edit_bill_item(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    return JSON_response({});        

@ login_required
def remove_bill_item(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # data contains only id:<item_id>
    try:
        data = JSON_parse(request.POST.get('data'))
    except:
        return JSON_error(_("No data in POST"))
        
    # get item and remove it
    try:

        item = BillItem.objects.get(id=int(data.get('id')))
        # save item id for later
        id = item.id
        item.delete()
        return JSON_response({'status':'ok', 'id':id})
    except:
        return JSON_error(_("Could not delete the item"))
