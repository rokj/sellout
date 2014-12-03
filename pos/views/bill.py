from datetime import datetime as dtm
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import FieldDoesNotExist
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from pytz import timezone

from pos.models import Company, Product, Discount, Register, Contact, \
    Bill, BillCompany, BillContact, BillRegister, BillItem, BillItemDiscount
from pos.views.manage.company import company_to_dict
from pos.views.manage.contact import contact_to_dict
from pos.views.manage.register import register_to_dict
from pos.views.util import has_permission, JsonOk, JsonParse, JsonError, \
    format_number, parse_decimal, format_date, format_time, parse_decimal_exc, max_field_length
from config.functions import get_company_value
import common.globals as g

from printing.escpos import escpostext


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

    i['base'] = format_number(user, company, item.base)
    i['quantity'] = format_number(user, company, item.quantity)
    i['tax_rate'] = format_number(user, company, item.tax_rate)

    i['batch'] = format_number(user, company, item.batch)
    i['discount'] = format_number(user, company, item.discount)
    i['net'] = format_number(user, company, item.net)
    i['tax'] = format_number(user, company, item.tax)
    i['total'] = format_number(user, company, item.total)

    # if group_tax_rates() was called on a list with this item in it,
    # there should be tax_rate_id property on the item. if it's not, f**k it,
    # the calling function won't use it anyway
    try:
        i['tax_rate_id'] = item.tax_rate_id
    except (AttributeError, FieldDoesNotExist):
        pass

    return i


def group_tax_rates(items):
    # check if items is a list:
    # if it's not
    if not isinstance(items, type([])):
        raise TypeError("Items is not a list, convert with list(items) in calling function")

    rate_id = 'A'  # tax rate id

    rates = {}  # rate: {letter, tax_sum, gross_sum}
    sums = {  # total of all items
        'net_sum': Decimal(0),
        'tax_sum': Decimal(0),
        'gross_sum': Decimal(0),
    }

    for item in items:
        t = item.tax_rate

        # totals
        sums['net_sum'] += item.net
        sums['tax_sum'] += item.tax
        sums['gross_sum'] += item.total

        # by each tax rate
        if t not in rates:
            # create a new entry in the list of taxes
            rates[t] = {
                'id': rate_id,
                'amount': item.tax_rate,
                'tax_sum': item.tax,
                'net_sum': item.net,
                'gross_sum': item.total,
            }

            # save to the item object for later use
            item.tax_rate_id = rate_id

            # get the next id
            rate_id = chr(ord(rate_id) + 1)
        else:
            # add a new tax rate to the list (dictionary, actually)
            rates[t]['tax_sum'] += item.tax
            rates[t]['net_sum'] += item.net
            rates[t]['gross_sum'] += item.total

            # save to the item object for later use
            item.tax_rate_id = rates[t]['id']

    # convert rates to list and order by id
    rates = sorted(rates.iteritems())
    rates = [i[1] for i in rates]  # we're only interested in content, keys are already there

    # that's it
    return {'rates': rates, 'sums': sums}


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
    b = {
        'id': bill.id,

        'issuer': company_to_dict(bill.issuer),
        'register': register_to_dict(user, company, bill.register),

        'user_id': str(bill.user_id),
        'user_name': str(bill.user_name),

        'serial': bill.serial,
        'notes': bill.notes,


        'discount_amount': format_number(user, company, bill.discount_amount),
        'discount_type': bill.discount_type,

        # prices
        'currency': bill.currency,
        'base': format_number(user, company, bill.base),
        'discount': format_number(user, company, bill.discount),
        'tax': format_number(user, company, bill.tax),
        'total': format_number(user, company, bill.total),

        'timestamp': format_date(user, company, bill.timestamp) + " " + format_time(user, company, bill.timestamp),
        'status': bill.status,

    }

    if bill.contact:
        b['contact'] = contact_to_dict(user, company, bill.contact)

    # get items
    items = list(BillItem.objects.filter(bill=bill))

    # gather tax rates for all items
    grouped_taxes = group_tax_rates(items)
    tax_rates = grouped_taxes['rates']
    tax_sums = grouped_taxes['sums']

    for rate in tax_rates:
        rate['amount'] = format_number(user, company, rate['amount'])
        rate['tax_sum'] = format_number(user, company, rate['tax_sum'])
        rate['net_sum'] = format_number(user, company, rate['net_sum'])
        rate['gross_sum'] = format_number(user, company, rate['gross_sum'])

    tax_sums['tax_sum'] = format_number(user, company, tax_sums['tax_sum'])
    tax_sums['net_sum'] = format_number(user, company, tax_sums['net_sum'])
    tax_sums['gross_sum'] = format_number(user, company, tax_sums['gross_sum'])

    b['tax_rates'] = tax_rates
    b['tax_sums'] = tax_sums

    # format all items
    i = []
    for item in items:
        i.append(bill_item_to_dict(user, company, item))
        
    b['items'] = i

    return b


def create_bill_html(user, company, bill):
    # get the template and some other details
    logo = None

    if bill.register.receipt_format == 'Page':
        t = 'pos/large_receipt.html'

        if company.color_logo:
            logo = company.color_logo.url

    elif bill.register.receipt_format == 'Thermal':
        t = 'pos/small_receipt.html'

        if company.monochrome_logo:
            logo = company.monochrome_logo.url

    else:
        return _("Unsupported bill format") + ": " + str(bill.register.receipt_format)

    # get the data
    bill_data = bill_to_dict(user, company, bill)

    context = {
        'bill': bill_data,
        'logo': logo,
    }

    return render_to_string(t, context)


#########
# views #
#########

@login_required
def create_bill(request, company):
    """ there's bill and items in request.POST['data'], create a new bill, and check all items and all """

    def item_error(message, product):
        return JsonError(message + " " + _("(Item" + ": ") + product.name + ")")

    # get company
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions
    if not has_permission(request.user, c, 'bill', 'edit'):
        return JsonError(_("You have no permission to create bills"))

    # get data
    data = JsonParse(request.POST.get('data'))
    if not data:
        return JsonError(_("No data received"))

    # see if we're updating an existing bill
    existing_bill = None
    try:
        existing_bill = Bill.objects.get(company=c, id=int(data.get('id')))
        if existing_bill.status == 'Paid':
            return JsonError(_("This bill has already been paid, editing is not possible"))
    except (ValueError, TypeError):
        pass
    except Bill.DoesNotExist:
        pass

    # current company (that will be fixed on this bill forever):
    # save a FK to BillCompany; the last company is the current one
    bill_company = BillCompany.objects.filter(company=c).order_by('-datetime_created')[0]

    # current register: get BillRegister with the same id as current one
    try:
        bill_registers = BillRegister.objects.filter(register__id=int(data.get('register_id')))
        if len(bill_registers) > 0:
            bill_register = bill_registers[0]
        else:
            raise Register.DoesNotExist
    except (TypeError, ValueError, Register.DoesNotExist):
        return JsonError(_("Invalid register specified."))

    # current contact: get BillContact with the same id as the requested contact
    if data.get('contact'):
        try:
            bill_contacts = BillContact.objects.get(contact__id=int(data.get('contact').get('id'))).order_by('datetime_created')
            if len(bill_contacts) > 0:
                bill_contact = bill_contacts[0]
            else:
                raise Contact.DoesNotExist
        except (Contact.DoesNotExist, ValueError, TypeError):
            return JsonError(_("Invalid contact"))
    else:
        bill_contact = None

    # save all validated stuff in bill to a dictionary and insert into database at the end
    # prepare data for insert
    bill = {
        'company': c,
        'issuer': bill_company,
        'register': bill_register,
        'contact': bill_contact,
        'user_id': request.user.id,
        'user_name': str(request.user),
        'notes': data.get('notes')[:max_field_length(Bill, 'notes')],

        'timestamp': dtm.now(),
        'type': "Normal",
        'status': "Unpaid",  # the bill is awaiting payment, a second request on the server will confirm it
        'items': [],
        'currency': get_company_value(request.user, c, 'pos_currency'),
    }

    r = parse_decimal(request.user, c, data.get('total'))
    if not r['success'] or r['number'] <= Decimal('0'):
        return JsonError(_("Invalid grand total value"))
    else:
        grand_total = r['number']

    # validate items
    for i in data.get('items'):
        # get product
        try:
            product = Product.objects.get(company=c, id=int(i.get('product_id')))
        except Product.DoesNotExist:
            return JsonError(_("Product with this id does not exist") + " (id=" + i.get('product_id') + ")")

        # parse quantity
        r = parse_decimal(request.user, c, i.get('quantity'), g.DECIMAL['quantity_digits'])
        if not r['success']:
            return item_error(_("Invalid quantity value"), product)
        else:
            if r['number'] <= Decimal('0'):
                return item_error(_("Cannot add an item with zero or negative quantity"), product)
        quantity = r['number']

        # remove from stock; TODO: check negative quantities (?)
        product.stock = product.stock - quantity
        product.save()

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
            'bill_notes': i.get('bill_notes'),

            'discounts': [],  # validated discounts (FK in database)

            # prices: will be calculated after discounts are ready
            'base': None,
            'quantity': None,
            'tax_rate': None,
            'batch': None,
            'discount': None,
            'net': None,
            'tax': None,
            'total': None,
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

            # amount: parse number and check that percentage does not exceed 100%
            r = parse_decimal(request.user, c, d.get('amount'))
            if not r['success']:
                return item_error(_("Invalid discount amount"), product)
            else:
                d_amount = r['number']
                if d_amount < Decimal(0) or (d.get('type') == 'Relative' and d_amount > Decimal(100)):
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

        # save this item's prices to item's dictionary (will go into database later)
        try:
            item['base'] = parse_decimal_exc(request.user, c, i.get('base'), message=_("Invalid base price"))
            item['quantity'] = parse_decimal_exc(request.user, c, i.get('quantity'), message=_("Invalid quantity"))
            item['tax_rate'] = parse_decimal_exc(request.user, c, i.get('tax_rate'), message=_("Invalid tax rate"))
            item['batch'] = parse_decimal_exc(request.user, c, i.get('batch'), message=_("Invalid batch price"))
            item['discount'] = parse_decimal_exc(request.user, c, i.get('discount'), message=_("Invalid discount amount"))
            item['net'] = parse_decimal_exc(request.user, c, i.get('net'), message=_("Invalid net price"))
            item['tax'] = parse_decimal_exc(request.user, c, i.get('tax'), message=_("Invalid tax amount"))
            item['total'] = parse_decimal_exc(request.user, c, i.get('total'), message=_("Invalid total"))
        except ValueError as e:
            return item_error(e.message, product)

    # at this point, everything is fine, insert into database

    if existing_bill:
        existing_bill.delete()

    # create a new bill
    db_bill = Bill(
        created_by=request.user,
        company=c,  # current company, FK to Company object
        issuer=bill['issuer'],  # fixed company details at this moment, FK to BillCompany object
        user_id=bill['user_id'],  # id of user that created this bill, just an integer, not a FK
        user_name=bill['user_name'],  # copied user name in case that user gets 'fired'
        register=bill['register'],  # current settings of the register this bill was created on
        contact=bill['contact'],  # FK on BillContact, copy of the Contact object
        notes=bill['notes'],
        currency=bill['currency'],

        timestamp=dtm.now().replace(tzinfo=timezone(get_company_value(request.user, c, 'pos_timezone'))),
        status=bill['status'],
        total=grand_total
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
            bill_notes=item['bill_notes'],
            product_id=item['product_id'],

            quantity=item['quantity'],
            base=item['base'],
            tax_rate=item['tax_rate'],

            batch=item['batch'],
            discount=item['discount'],
            net=item['net'],
            tax=item['tax'],
            total=item['total'],
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
    return JsonOk(extra=d)


@login_required
def get_unpaid_bills(request, company):
    """ returns unpaid bill for the company, if there's any """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'bill', 'view'):
        return JsonError(_("You have no permission to view bills"))

    # return a list of bills
    unfinished_bills = Bill.objects.filter(company=c).exclude(status='Paid').order_by('-timestamp')

    bills = []
    for b in unfinished_bills:
        bills.append(bill_to_dict(request.user, c, b))

    return JsonOk(extra=bills)


@login_required
def delete_unpaid_bill(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # bill_id is required in request.POST
    try:
        bill_id = int(JsonParse(request.POST.get('data')).get('bill_id'))
        bill = Bill.objects.get(company=c, id=bill_id)
    except (TypeError, ValueError):
        return JsonError(_("Invalid bill id"))
    except Bill.DoesNotExist:
        return JsonError(_("Bill does not exist"))

    # check if this user has permission to edit bills
    if not has_permission(request.user, c, 'bill', 'edit'):
        return JsonError(_("You have no permission to edit bills"))

    # check if this bill is really unpaid
    if bill.status != 'Unpaid':
        return JsonError(_("This bill has already been paid, deleting is not possible"))

    # if everything is ok, delete it and send an OK message
    bill.delete()
    return JsonOk()


@login_required
def check_bill_status(request, company):
    """
        check if the bill has been paid and return the status
    """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # there should be bill_id in request.POST
    try:
        bill_id = int(JsonParse(request.POST.get('data')).get('bill_id'))
        bill = Bill.objects.get(company=c, id=bill_id)
    except (Bill.DoesNotExist, ValueError, TypeError):
        return JsonError(_("Bill does not exist or data is invalid"))

    if bill.status == 'Paid':
        return JsonOk(extra={'paid': True})
    else:
        return JsonOk(extra={'paid': False})


@login_required
def finish_bill(request, company, android=False):
    """
        find the bill, update its status and set payment type and reference
    """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'bill', 'edit'):
        return JsonError(_("You have no permission to edit bills"))

    # data must contain: bill_id, status, payment_type, payment_reference
    d = JsonParse(request.POST.get('data'))

    if not d or not d.get('bill_id'):
        return JsonError(_("No data in request"))

    # bill...
    try:
        bill = Bill.objects.get(company=c, id=int(d.get('bill_id')))
    except (ValueError, TypeError, Bill.DoesNotExist):
        return JsonError(_("No bill found"))

    # check status: if 'Paid', set payment type and reference;
    # if 'Canceled', just update status
    if d.get('status') == 'Paid':
        # check payment type
        if d.get('payment_type') not in [x[0] for x in g.PAYMENT_TYPES]:
            return JsonError(_("Payment type does not exist"))

        bill.status = 'Paid'
        bill.payment_type = d.get('payment_type')
        # payment reference: if paid with bitcoin - btc address, if paid with cash, cash amount given
        bill.payment_reference = d.get('payment_reference')
    else:
        bill.status = 'Canceled'

    bill.save()

    # if print is requested, return html, otherwise the 'ok' response
    if d.get('print'):
        return JsonResponse({'status': 'ok',
                             'print': esc_format(bill, esc_commands=True),
                             'bill': create_bill_html(request.user, c, bill)})

    return JsonOk()


@login_required
def view_bill(request, company):
    """ returns html-formatted bill """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # expect the following in request.GET:
    # bill_id: id of Bill object
    # format: receipt_format setting from register
    try:
        bill_id = int(request.GET.get('bill_id'))
    except (ValueError, TypeError):
        return JsonError(_("Missing required data"))

    # get the bill
    try:
        bill = Bill.objects.get(company=c, id=bill_id)
    except Bill.DoesNotExist:
        return JsonError(_("Bill does not exist"))

    return HttpResponse(create_bill_html(request.user, c, bill))

def esc_format(bill, format, line_char_no=42, esc_commands=False):
    if format == g.RECEIPT_FORMATS[0]:
        return 'full_page_format'
    elif format == g.RECEIPT_FORMATS[1]:
        string = ''

        if esc_commands:
            printer = escpostext.EscposText()
            # center / bold
            string += printer.set(align='center', bold='True')
            string += printer.text(bill.issuer.name + constants.CTRL_LF)
            string += printer.set(bold='False')
            # center
            string += printer.text(bill.issuer.street + ' ' + bill.issuer.street + ' ' + bill.issuer.city + constants.CTRL_LF)
            string += printer.text(bill.issuer.state + ' ' + bill.issuer.country + constants.CTRL_LF)

            string += printer.text(_('VAT') + ':' + ' ' + bill.issuer.vat_no + constants.CTRL_LF)
            string += constants.CTRL_LF

            string += printer.text(bill.register.location + constants.CTRL_LF)

            if bill.contact:
                string += printer.text(bill.contact.name + constants.CTRL_LF)
                string += printer.text(bill.contact.street + ' ' + bill.contact.postcode + ' ' + bill.contact.city + constants.CTRL_LF)
                string += printer.text(bill.contact.state + ' ' + bill.contact.country + constants.CTRL_LF)
                string += printer.text(_('VAT') + ':' + ' ' + bill.contact.vat_no + constants.CTRL_LF)

            string += printer.text(_('Bill No.') + ' ' + bill.serial)
            string += printer.line(line_char_no=line_char_no)

            white_spaces = [0.25, 0.15, 0.1, 0.2, 0.25, 0.05]

            temp_s = list(' '*line_char_no)
            price_s = _('Price')
            qty_s = _('Qty')
            unit_s = ''
            discount_s = _('Discount')
            amount_s = _('Amount')

            price_n = sum(white_spaces[:1])*line_char_no
            qty_n = sum(white_spaces[:2]*line_char_no)
            unit_n = sum(white_spaces[:3]*line_char_no)
            discount_n = sum(white_spaces[:4]*line_char_no)
            amount_n = sum(white_spaces[:5]*line_char_no)

            temp_s[price_n-len(price_s):price_n] = price_s
            temp_s[qty_n-len(qty_s):qty_n] = qty_s
            temp_s[unit_n-len(unit_s):unit_n] = unit_s
            temp_s[discount_n-len(discount_s):discount_n] = discount_s
            temp_s[amount_n-len(amount_s):amount_n] = amount_s

            string += "".join(temp_s)
            string += printer.line(line_char_no=line_char_no)

            for item in bill.items:

                string += item.name + constants.CTRL_LF

                temp_s = list(' '*line_char_no)

                temp_s[price_n-len(item.base_price):price_n] = item.base_price
                temp_s[qty_n-len(item.quantity):qty_n] = item.quantity
                temp_s[unit_n-len(''):unit_n] = ''
                temp_s[discount_n-len(item.discount_absolute):discount_n] = item.discount_absolute
                temp_s[amount_n-len(item.tax_rate_id):amount_n] = item.tax_rate_id

                string += "".join(temp_s)

            string += printer.line(line_char_no=line_char_no)

            temp_s = list(' '*line_char_no)
            total = _('Total') + ' ' + bill.currency + ':'
            temp_s[0:] = total
            temp_s[line_char_no-len(bill.total):] = bill.total
            string += "".join(temp_s)

            string += printer.line(line_char_no=line_char_no)

            temp_s = list(' '*line_char_no)

            white_spaces = [0.08, 0.22, 0.23, 0.23, 0.23]

            rate_s = _('Rate')
            subtotal_s = _('Subtotal')
            tax_s = _('Tax')
            total_s = _('Total')

            rate_id_n = sum(white_spaces[1]*line_char_no)
            rate_n = sum(white_spaces[:2])*line_char_no
            subtotal_n = sum(white_spaces[:3]*line_char_no)
            tax_n = sum(white_spaces[:4]*line_char_no)
            total_n = sum(white_spaces[:5]*line_char_no)

            temp_s[rate_n-len(rate_s):rate_n] = rate_s
            temp_s[subtotal_n-len(subtotal_s):subtotal_n] = subtotal_s
            temp_s[tax_n-len(tax_s):tax_n] = tax_s
            temp_s[total_n-len(total_s):total_n] = total_s

            string += "".join(temp_s)

            string += printer.line(line_char_no=line_char_no, style='Dotted')
            for rate in bill.tax_rates:
                temp_s = list(' '*line_char_no)
                temp_s[rate_id_n-len(rate.id)] = rate.id
                temp_s[rate_n-len(rate.amount):rate_n] = rate.amount
                temp_s[subtotal_n-len(rate.net_sum):subtotal_n] = rate.net_sum
                temp_s[tax_n-len(rate.tax_sum):tax_n] = rate.tax_sum
                temp_s[total_n-len(rate.gross_sum):total_n] = rate.gross_sum

                string += "".join(temp_s)

                string += printer.line(line_char_no=line_char_no, style='Dotted')

            sum = _('Sum')

            temp_s = list(' '*line_char_no)
            temp_s[rate_id_n-len(sum)] = sum
            temp_s[subtotal_n-len(bill.tax_sums.net_sum):subtotal_n] = bill.tax_sums.net_sum
            temp_s[tax_n-len(bill.tax_sums.tax_sum):tax_n] = bill.tax_sums.tax_sum
            temp_s[total_n-len(bill.tax_sums.gross_sum):total_n] = bill.tax_sums.gross_sum

            string += "".join(temp_s)

            temp_s = list(' '*line_char_no)
            total = _('Cashier') + ' ' + bill.user_name + ':'
            temp_s[0:] = total
            temp_s[line_char_no-len(bill.timestamp):] = bill.timestamp
            string += "".join(temp_s)

            return string

        return 'thermal_page_format'

    return