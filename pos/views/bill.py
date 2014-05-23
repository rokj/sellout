#
# Bill
#   ajax views:
#     get_active_bill: finds an unfinished bill and returns it (returns a new bill if none was found)
#     add_item: adds an item to bill
#     edit_item: edits an existing item
#     delete_item
#
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.utils.translation import ugettext as _

from pos.models import Company, Bill, BillItem, Product
from pos.views.util import has_permission, JSON_response, JSON_ok, JSON_parse, JSON_error, \
    format_number, parse_decimal, format_date, format_time
from config.functions import get_value
import common.globals as g

from pytz import timezone
from datetime import datetime as dtm
from decimal import Decimal


def bill_item_to_dict(user, item):
    i = {}
    
    i['item_id'] = item.id

    # values from product
    i['product_id'] = item.product_id
    i['code'] = item.code
    i['shortcut'] = item.shortcut
    i['name'] = item.name
    i['description'] = item.description
    i['private_notes'] = item.private_notes
    i['unit_type'] = item.unit_type
    i['stock'] = format_number(user, item.stock)
    # values from bill Item
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
    b['bill_id'] = bill.id
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
        company=company,
        user=user,  # this can change
        created_by=user,  # this will never change
        type="Normal",
        timestamp=dtm.now().replace(tzinfo=timezone(get_value(user, 'pos_timezone'))),
        status="Active"
    )
    b.save()

    return bill_to_dict(user, b)


def validate_prices():

    pass


def item_prices(user, base_price, tax_percent, quantity, discounts):
    """ calculates prices and stuff and return the data
        passing parameters instead of Item object because Item may not exist yet
    """
    def get_discount(p):
        """
            accumulates discounts on price p and returns final price and discounts
        """

        discount = Decimal('0') # cumulative discounts
        final = p # the final price

        for di in discounts:
            if di.type == 'Absolute':
                final = final - di.amount
                discount = discount + di.amount
            else:
                this_discount = final*(di.amount/100)
                discount += this_discount
                final -= this_discount

        return {'discount': discount, 'final': final}

    r = {}  # return values

    if get_value(user, 'pos_discount_calculation') == 'Tax first':
        # price without tax and discounts
        r['base'] = base_price
        # price including tax
        r['tax_price'] = base_price*(Decimal('1') + (tax_percent/Decimal('100')))
        # absolute tax value
        r['tax_absolute'] = r['tax_price'] - r['base']
        # absolute discounts value
        dd = get_discount(r['tax_price'])
        r['discount_absolute'] = dd['discount']
        # total, including tax and discounts
        r['total'] = dd['final']
        # total excluding tax
        r['total_tax_exc'] = r['total'] - r['tax_absolute']
    else:
        # base price
        r['base'] = base_price
        # subtract discounts from base
        dd = get_discount(r['tax_price'])
        r['discount'] = dd['discount']
        # price including discounts
        r['discount_price'] = dd['final']
        # add tax
        r['tax_price'] = r['discount_price']*(Decimal('1') + (tax_percent/Decimal('100')))
        # get absolute tax value
        r['tax_absolute'] = r['tax_price'] - r['discount_price']
        # total
        r['total'] = r['tax_price']
        # total without tax
        r['total_tax_exc'] = r['discount_price']

    # multiply everything by quantity
    r['base'] = r['base']*quantity  # without tax and discounts
    r['tax_absolute'] = r['tax_absolute']*quantity  # tax, absolute
    r['discount_absolute'] = r['discount_absolute']*quantity  # discounts, absolute
    r['total_tax_exc'] = r['total_tax_exc']*quantity  # total without tax
    # save single total
    r['single_total'] = r['total']
    r['total'] = r['total']*quantity  # total total total

    return r


def validate_bill_item(data):
    """ TODO: finds bill and item in database and """
    pass


#########
# views #
#########
@login_required
@transaction.atomic
def create_bill(request, company):
    """ there's bill and items in request.POST['data'], create a new bill, and check all items and all """

    # get company
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # check permissions
    if not has_permission(request.user, c, 'bill', 'edit'):
        return JSON_error(_("You have no permission to create bills"))

    # get data
    d = JSON_parse(request.POST.get('data'))
    if not d:
        return JSON_error(_("No data received"))

    # check bill properties
    # TODO: ... (nothing to check?)

    # check items
    # TODO: ... (nothing to check?)

    # create a new bill
    try:
        with transaction.atomic():
            bill = Bill(
                company=c,
                user=request.user,  # this can change
                created_by=request.user,  # this will never change
                type="Normal",
                timestamp=dtm.now().replace(tzinfo=timezone(get_value(request.user, 'pos_timezone'))),
                status="Active"
            )
            bill.save()
            #try:

            #except:
            #    return JSON_error(_("Error while saving new bill"))

            # create new items
            print d.get('items')
            for i in d.get('items'):
            # get product
                try:
                    product = Product.objects.get(company=c, id=int(i.get('product_id')))
                except Product.DoesNotExist:
                    return JSON_error(_("Product with this id does not exist"))


                # parse quantity
                r = parse_decimal(request.user, i.get('quantity'), g.DECIMAL['quantity_digits'])
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
                discounts = product.get_discounts()
                prices = item_prices(request.user, product.get_price(), product.tax.amount, quantity, discounts)

                # notes, if any
                bill_notes = i.get('notes')

                # TODO: subtract quantity from stock (if there's enough left)
                # TODO: TODO

                # create a bill item and save it to database, then return JSON with its data
                item = BillItem(
                    created_by=request.user,
                    # copy ProductAbstract's values:
                    code=product.code,
                    shortcut=product.shortcut,
                    name=product.name,
                    description=product.description,
                    private_notes=product.private_notes,
                    unit_type=product.get_unit_type_display(), # ! display, not the 'code'
                    stock=product.stock,
                    # billItem's fields
                    bill=bill,
                    product_id=product.id,
                    quantity=quantity,
                    base_price=prices['base'],
                    tax_percent=product.tax.amount,
                    tax_absolute=prices['tax_absolute'],
                    discount_absolute=prices['discount_absolute'],
                    single_total=prices['single_total'],
                    total=prices['total'],
                    bill_notes=bill_notes
                )

                item.save()


    except IntegrityError:
        return JSON_error(_("Could not save one of items"))  # TODO: a bit more specific, please
    return JSON_ok()


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
    bill = bill_to_dict(request.user, bill)
    return JSON_response({'status': 'ok', 'bill': bill})


@DeprecationWarning
@login_required
def edit_item(request, company):
    """ add an item to bill:
         - received data: {item_id, bill_id, 'product_id':<id>, 'qty':<qty>, 'notes':<notes>}
         - calculate all item's fields (tax, discount, total, ...)
         - add to bill object
         - return item_to_dict
    """
    try:
        c = Company.objects.get(url_name=company)
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
    discounts = product.get_discounts()
    prices = item_prices(request.user, product.get_price(), product.tax.amount, quantity, discounts)

    # notes, if any    
    bill_notes = data.get('notes')

    # TODO: subtract quantity from stock (if there's enough left)

    # create a bill item and save it to database, then return JSON with its data
    item = BillItem(
        created_by=request.user,
        # copy ProductAbstract's values:
        code=product.code,
        shortcut=product.shortcut,
        name=product.name,
        description=product.description,
        private_notes=product.private_notes,
        unit_type=product.get_unit_type_display(),  # ! display, not the 'code'
        stock=product.stock,
        # billItem's fields
        bill=bill,
        product_id=product.id,
        quantity=quantity,
        base_price=prices['base'],
        tax_percent=product.tax.amount,
        tax_absolute=prices['tax_absolute'],
        discount_absolute=prices['discount_absolute'],
        single_total=prices['single_total'],
        total=prices['total'],
        bill_notes=bill_notes
    )
    item.save()

    # return the item in JSON
    return JSON_response({'item': bill_item_to_dict(request.user, item), 'status': 'ok'})


@ login_required
def remove_item(request, company):
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
        # save Item id for later
        id = item.id
        item.delete()
        return JSON_response({'status':'ok', 'item_id':id})
    except:
        return JSON_error(_("Could not delete the item"))
