#
# Bill
#   ajax views:
#     get_active_bill: finds an unfinished bill and returns it (returns a new bill if none was found)
#     add_item: adds an item to bill
#     edit_item: edits an existing item
#     delete_item
#
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from pos.models import Company, Bill, BillItem, Product, Discount, BillItemDiscount, Register
from pos.views.util import has_permission, JSON_response, JSON_ok, JSON_parse, JSON_error, \
    format_number, parse_decimal, format_date, format_time
from config.functions import get_company_value
import common.globals as g

from pytz import timezone
from datetime import datetime as dtm
from decimal import Decimal, getcontext, ROUND_HALF_UP


def bill_item_to_dict(user, company, item):
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
    i['stock'] = format_number(user, company, item.stock)

    # values from bill Item
    i['bill_id'] = item.bill.id
    i['bill_notes'] = item.bill_notes

    i['quantity'] = format_number(user, company, item.quantity)

    # these values are for one unit (not multiplied by quantity)
    i['base_price'] = format_number(user, company, item.base_price)
    i['tax_percent'] = format_number(user, company, item.tax_percent)
    i['single_total'] = format_number(user, company, item.single_total)

    i['tax_absolute'] = format_number(user, company, item.tax_absolute)
    i['discount_absolute'] = format_number(user, company, item.discount_absolute)
    i['total'] = format_number(user, company, item.total)
    i['total_without_tax'] = format_number(user, company, item.total - item.tax_absolute)

    return i


def bill_to_dict(user, company, bill):
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
    b['serial'] = bill.serial
    b['till_id'] = bill.till.id
    b['type'] = bill.type
    b['recipient_contact'] = bill.recipient_contact
    b['note'] = bill.note
    b['sub_total'] = format_number(user, company, bill.sub_total)
    b['discount'] = format_number(user, company, bill.discount)
    b['tax'] = format_number(user, company, bill.tax)
    b['total'] = format_number(user, company, bill.total)
    b['timestamp'] = format_date(user, company, bill.timestamp) + " " + format_time(user, company, bill.timestamp)
    b['due_date'] = format_date(user, company, bill.due_date)
    b['status'] = bill.status
    
    # items:
    items = BillItem.objects.filter(bill=bill)
    i = []
    for item in items:
        i.append(bill_item_to_dict(user, company, item))
        
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
        timestamp=dtm.now().replace(tzinfo=timezone(get_company_value(user, company, 'pos_timezone'))),
        status="Active"
    )
    b.save()

    return bill_to_dict(user, company, b)


def validate_prices():

    pass


def item_prices(user, company, base_price, tax_percent, quantity, discounts):
    """ calculates prices and stuff and return the data
        passing parameters instead of Item object because Item may not exist yet
        discount is a list of dictionaries (not Discount objects!)
    """
    def get_discount(p):
        """
            accumulates discounts on price p and returns final price and discounts
        """

        discount = Decimal('0')  # cumulative discounts
        final = p  # the final price

        for di in discounts:
            if di['type'] == 'Absolute':
                final = final - di['amount']
                discount = discount + di['amount']
            else:
                this_discount = final*(di['amount']/100)
                discount += this_discount
                final -= this_discount

        return {'discount': discount, 'final': final}

    # round up:
    getcontext().rounding = ROUND_HALF_UP

    r = {}  # return values

    if get_company_value(user, company, 'pos_discount_calculation') == 'Tax first':
        # price without tax and discounts
        r['base_price'] = base_price
        # price including tax
        r['tax_price'] = base_price*(Decimal('1') + (tax_percent/Decimal('100')))
        # absolute tax value
        r['tax_absolute'] = r['tax_price'] - r['base_price']
        # absolute discounts value
        dd = get_discount(r['tax_price'])
        r['discount_absolute'] = dd['discount']
        # total, including tax and discounts
        r['total'] = dd['final']
        # total excluding tax
        r['total_tax_exc'] = r['total'] - r['tax_absolute']
    else:
        # base price
        r['base_price'] = base_price
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

    # multiply by quantity
    r['base_price'] = r['base_price']*quantity  # without tax and discounts
    r['tax_absolute'] = r['tax_absolute']*quantity  # tax, absolute
    r['discount_absolute'] = r['discount_absolute']*quantity  # discounts, absolute
    r['total_tax_exc'] = r['total_tax_exc']*quantity  # total without tax
    # save single total
    r['single_total'] = r['total']
    r['total'] = r['total']*quantity  # total total total

    # and round to current decimal places
    # https://docs.python.org/2/library/decimal.html#decimal-faq
    precision = Decimal(10) ** -int(get_company_value(user, company, 'pos_decimal_places'))

    r['base_price'] = r['base_price'].quantize(precision)
    r['tax_absolute'] = r['tax_absolute'].quantize(precision)
    r['discount_absolute'] = r['discount_absolute'].quantize(precision)
    r['total_tax_exc'] = r['total_tax_exc'].quantize(precision)
    r['single_total'] = r['single_total'].quantize(precision)
    r['total'] = r['total'].quantize(precision)

    return r


def validate_bill_item(data):
    """ TODO: finds bill and item in database and """
    pass


#########
# views #
#########
@login_required
def create_bill(request, company):
    """ there's bill and items in request.POST['data'], create a new bill, and check all items and all """

    def item_error(message, product):
        return JSON_error(message + " " + _("(Item" + ": ") + product.name + ")")

    # get company
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # check permissions
    if not has_permission(request.user, c, 'bill', 'edit'):
        return JSON_error(_("You have no permission to create bills"))

    # get data
    data = JSON_parse(request.POST.get('data'))
    if not data:
        return JSON_error(_("No data received"))

    # check bill properties
    r = parse_decimal(request.user, c, data.get('total'))
    if not r['success'] or r['number'] <= Decimal('0'):
        return JSON_error(_("Invalid grand total value"))
    else:
        # this number came from javascript
        total_js = r['number']

    try:
        print
        till = Register.objects.get(id=int(data.get('till_id')), company=c)
    except (TypeError, ValueError, Register.DoesNotExist):
        return JSON_error(_("Invalid register specified."))

    # this number will be calculated below;
    # both grand totals must match or... ???
    total_py = Decimal('0')

    # save all validated stuff in bill to a dictionary and insert into database at the end
    # prepare data for insert
    bill = {
        'company': c,
        'user': request.user,
        'till': till,
        'timestamp': dtm.now(),
        'type': "Normal",
        'status': "Saved",
        'items': [],
    }

    # validate items
    for i in data.get('items'):
        # get product
        try:
            product = Product.objects.get(company=c, id=int(i.get('product_id')))
        except Product.DoesNotExist:
            return JSON_error(
                _("Product with this id does not exist") +
                " (id=" + i.get('product_id') + ")")

        # parse quantity
        r = parse_decimal(request.user, c, i.get('quantity'), g.DECIMAL['quantity_digits'])
        if not r['success']:
            return item_error(_("Invalid quantity value"), product)
        else:
            if r['number'] <= Decimal('0'):
                return item_error(_("Cannot add an item with zero or negative quantity"), product)
        quantity = r['number']

        # check if there's enough items left in stock (must be at least zero =D)
        if product.stock < quantity:
            return item_error(_("Cannot sell more items than there are in stock"), product)

        # TODO: subtract quantity from stock (if there's enough left)

        item = {
            'created_by': request.user,
            'code': product.code,
            'shortcut': product.shortcut,
            'name': product.name,
            'description': product.description,
            'private_notes': product.private_notes,
            'unit_type': product.get_unit_type_display(),  # ! display, not the 'code'
            'stock': product.stock,
            # 'bill':  not now, after bill is saved
            'product_id': product.id,
            'quantity': quantity,
            'tax_percent': product.tax.amount,
            'bill_notes': i.get('bill_notes'),
            'discounts': [],  # validated discounts
            # prices: will be calculated after discounts are ready
            'base_price': i.get('base_price'),
            'tax_absolute': i.get('tax_absolute'),
            'discount_absolute': i.get('discount_absolute'),
            'single_total': i.get('single_total'),
            'total': i.get('total'),
        }

        bill['items'].append(item)

        for d in i['discounts']:
            # check:
            # discount id: if it's -1, it's a unique discount on this item;
            #              if it's anything else, the discount must belong to this company
            #              and must be active and enabled
            d_id = int(d.get('id'))
            if d_id != -1:
                try:
                    dbd = Discount.objects.get(id=d_id, company=c)

                    if not dbd.is_active:
                        return item_error(_("The discount is not active"), product)
                except Discount.DoesNotExist:
                    return item_error(_("Chosen discount does not exist or is not valid"), product)

            # discount type: must be in g.DISCOUNT_TYPES
            if d.get('type') not in [x[0] for x in g.DISCOUNT_TYPES]:
                return item_error(_("Wrong discount type"), product)

            # amount: parse number and check that percentage does not exceed 100%
            r = parse_decimal(request.user, c, d.get('amount'))
            if not r['success']:
                return item_error(_("Invalid discount amount"), product)
            else:
                d_amount = r['number']
                if d_amount < Decimal('0') or (d.get('type') == 'Percentage' and d_amount > Decimal('100')):
                    return item_error(_("Invalid discount amount"), product)

            # save data to bill
            discount = {
                'id': d_id,
                'code': d.get('code'),
                'description': d.get('description'),
                'type': d.get('type'),
                'amount': d_amount
            }
            item['discounts'].append(discount)

        # calculate this item's price
        prices = item_prices(request.user, c, product.get_price(), product.tax.amount, item['quantity'], item['discounts'])

        # check prices against price from javascript
        r = parse_decimal(request.user, c, i.get('total'))
        if not r['success']:
            return item_error(_("Item price is in wrong format"), product)
        else:
            if prices['total'] != r['number']:
                return item_error(_("Item prices do not match"), product)
            else:
                # add this price to grand total
                total_py += r['number']

        # save this item's prices to item's dictionary (will go into database later)
        item['base_price'] = prices['base_price']
        item['tax_absolute'] = prices['tax_absolute']
        item['discount_absolute'] = prices['discount_absolute']
        item['single_total'] = prices['single_total']
        item['total'] = prices['total']

    # in the end, check grand totals against each others
    if total_js != total_py:
        return JSON_error(_("Total prices do not match"))

    # at this point, everything is fine, insert into database

    # create a new bill
    db_bill = Bill(
        company=c,
        user=bill['user'],  # this can change
        till=till,
        created_by=bill['user'],  # this will never change
        type=bill['type'],
        timestamp=dtm.now().replace(tzinfo=timezone(get_company_value(request.user, c, 'pos_timezone'))),
        status=bill['status'],
        total=total_py
    )
    db_bill.save()

    # create new items
    for item in bill['items']:
        db_item = BillItem(
            created_by=item['created_by'],
            code=item['code'],
            shortcut=item['shortcut'],
            name=item['name'],
            description=item['description'],
            private_notes=item['private_notes'],
            unit_type=item['unit_type'],
            stock=item['stock'],
            bill=db_bill,
            product_id=item['product_id'],
            quantity=item['quantity'],
            base_price=item['base_price'],
            tax_percent=item['tax_percent'],
            tax_absolute=item['tax_absolute'],
            discount_absolute=item['discount_absolute'],
            single_total=item['single_total'],
            total=item['total'],
            bill_notes=item['bill_notes']
        )
        db_item.save()

        # save discounts for this item
        for discount in item['discounts']:
            db_discount = BillItemDiscount(
                created_by=request.user,
                bill_item=db_item,

                description=discount['description'],
                code=discount['code'],
                type=discount['type'],
                amount=discount['amount']
            )
            db_discount.save()

    d = {'bill': bill_to_dict(request.user, c, db_bill)}
    return JSON_ok(extra=d)


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
    bill = bill_to_dict(request.user, c,  bill)
    return JSON_response({'status': 'ok', 'bill': bill})
