from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pos.models import Company, Bill, BillItem, Price
from pos.views.manage import get_all_categories_structured

from pos.views.util import has_permission, no_permission_view, JSON_response, JSON_ok, JSON_parse, JSON_error, \
                           format_number, parse_decimal, format_date, format_time
from config.functions import get_value, set_value
import common.globals as g

import json
from pytz import timezone
from datetime import datetime as dtm

def get_item_price():
    pass

def bill_item_to_dict(user, item):
    # fields in bill_item: (all fields are Decimal)
    
    # bill (id > bill FK)   
    # quantity              |
    # base_price            |
    # tax_absolute          | all Decimal fields
    # discount_absolute     |
    # total                 |
    # bill_notes            
    i = {}
    
    i['id'] = item.id
    i['bill'] = item.bill.id
    i['quantity'] = format_number(user, item.quantity)
    i['base_price'] = format_number(user, item.base_price)
    i['tax_absolute'] = format_number(user, item.tax_absolute)
    i['discount_absolute'] = format_number(user, item.discount_absolute)
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
        i.append(bill_item_to_dict(user, i))
        
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
    bdict['new'] = True

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
def add_item_to_bill(request, company):
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
        
    # get bill
    try:
        bill = Bill.objects.get(company=c, id=request.POST.get('data').get('bill'))
    except Bill.DoesNotExist:
        return JSON_error(_("This bill does not exist"))
    
    # get product
    try:
        product = Product.objects.get(company=c, id=int(request.POST.get('data').get('product_id')))
    except Product.DoesNotExist:
        return JSON_error(_("Product with this id does not exist"))

    # parse quantity    
    r = parse_decimal(request.user, request.POST.get('data').get('qty'), g.DECIMAL['quantity_digits'])
    if not r['success']:
        return JSON_error(_("Invalid quantity value"))
    else:
        if r['number'] <= Decimal('0'):
            return JSON_error(_("Cannot add an item with zero or negative quantity"))
    quantity = r['number']
            
    # calculate and set all stuff for this new item:
    # bill (already checked)
    # quantity (already_checked)
    try:
        base_price = Price.objects.filter(product=product).order_by('-datetime_updated')[0].unit_price
    except Price.DoesNotExist:
        return JSON_error(_("Price for this product is not defined"))
    
    # tax:
    tax = product.tax.amount
    
    # calculate discounts and tax: equation depends on configuration (first tax or first discounts)
    if get_value(request.user, 'pos_discount_calculation') == "Tax first":
        # first add tax to base price, then subtract discounts
        print 'tax first'
    else:
        # first subtract discounts from base price, then add tax
        print 'discount first'
    
    # tax_absolute = models.DecimalField(_("Tax amount (absolute value)"), # hard-coded price from current Price table
    # discount_absolute = models.DecimalField(_("Discount, absolute value, sum of all valid discounts on this product"), 
    # total = models.DecimalField(_("Total price"),
    
    bill_notes = request.POST.get('data').get('notes')

    
    
    
    
    
