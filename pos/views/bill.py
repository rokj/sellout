from datetime import datetime as dtm, datetime
from decimal import Decimal, ROUND_UP
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.template import TemplateDoesNotExist

from common.decorators import login_required
from django.db.models import FieldDoesNotExist
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string, get_template
from django.utils.translation import ugettext as _

from payment.models import Payment
from payment.service.Paypal import Paypal

from pos.models import Company, Product, Discount, Register, Contact, \
    Bill, BillCompany, BillContact, BillRegister, BillItem, BillItemDiscount
from pos.views.manage.company import company_to_dict
from pos.views.manage.contact import contact_to_dict
from pos.views.manage.register import register_to_dict
from common.functions import has_permission, JsonOk, JsonParse, JsonError, \
    format_number, parse_decimal, format_date, format_time, parse_decimal_exc, max_field_length
from config.functions import get_company_value
import common.globals as g

from printing.escpos import escpostext
import settings

import random


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

        'issuer': company_to_dict(user, bill.issuer),
        'register': register_to_dict(user, company, bill.register),

        'user_id': bill.user_id,
        'user_name': bill.user_name,

        'serial': bill.serial,
        'serial_prefix': bill.serial_prefix,
        'serial_number': bill.serial_number,
        'notes': bill.notes,

        'discount_amount': format_number(user, company, bill.discount_amount),
        'discount_type': bill.discount_type,
        'currency': bill.payment.currency,

        # prices
        'base': format_number(user, company, bill.base),
        'discount': format_number(user, company, bill.discount),
        'tax': format_number(user, company, bill.tax),
        'total': format_number(user, company, bill.total),

        'timestamp': format_date(user, company, bill.timestamp) + " " + format_time(user, company, bill.timestamp),
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

    b['payment'] = payment_to_dict(user, company, bill.payment)

    return b


def payment_to_dict(user, company, payment):
    return {
        'type': payment.type,
        'amount_paid': format_number(user, company, payment.amount_paid),
        'currency': payment.currency,
        'total': format_number(user, company, payment.total),
        'total_btc': format_number(user, company, payment.total_btc),
        'transaction_datetime': format_date(user, company, payment.transaction_datetime),
        'btc_transaction_reference': payment.btc_transaction_reference,
        'paypal_transaction_reference': payment.paypal_transaction_reference,
        'payment_info': payment.payment_info,
        'status': payment.get_status_display()
    }


def create_printable_bill(user, company, bill, receipt_format=None, esc=False):
    # get the template and some other details
    logo = None

    if not receipt_format:
        receipt_format = bill.register.receipt_format

    # choose the bill according to company's country
    t = 'pos/print/' + bill.company.country.lower() + '/'

    # choose receipt format
    if receipt_format == 'Page':
        t += 'large_receipt.html'

        if company.color_logo:
            logo = company.color_logo.url

    elif receipt_format == 'Thermal':
        t += 'small_receipt.html'

        if company.monochrome_logo:
            logo = company.monochrome_logo.url
    else:
        return {
            'status': 'Unsupported_bill_format',
            'message': _("Unsupported bill format") + ": " + str(bill.register.receipt_format)
        }

    # check if the template we've decided to need exists
    try:
        get_template(t)
    except TemplateDoesNotExist:
        return {
            'status': 'Template not found',
            'message': _("Template does not exist") + ": " + t
        }

    # get the data
    bill_data = bill_to_dict(user, company, bill)

    context = {
        'bill': bill_data,
        'logo': logo,
    }
    data = {
        'bill': bill_data,
        'html': render_to_string(t, context),
        'status': 'ok'
    }
    if esc:
        data['esc'] = esc_format(user, company, bill, receipt_format, esc_commands=True)

    return data


def create_bill_html(user, company, bill):
    data = create_printable_bill(user, company, bill)
    if data.get('status') == 'ok':
        return data['html']
    else:
        return data['message']


def esc_format(user, company, bill, bill_format, line_char_no=48, esc_commands=False):

    if bill_format == 'Page':
        return 'full_page_format'
    elif bill_format == "Thermal":
        string = ''
        if esc_commands:
            bill_dict = bill_to_dict(user, company, bill)
            printer = escpostext.EscposText()
            new_line = '\x0a'
            center_align = '\x1b\x61\x01'
            left_align = '\x1b\x61\x00'
            # center / bold
            string += center_align
            string += printer.text(bill_dict.get('issuer').get('name'))
            string += new_line
            # center
            string += printer.text(bill_dict.get('issuer').get('street') + ' ' + bill_dict.get('issuer').get('postcode') + ' ' + bill_dict.get('issuer').get('city'))
            string += new_line
            string += printer.text(bill_dict['issuer']['state'] + ' ' + bill_dict['issuer']['country'])
            string += new_line

            string += printer.text(_('VAT') + ':' + ' ' + bill_dict['issuer']['vat_no'])
            string += new_line

            string += printer.text(bill_dict['register']['location'])

            string += new_line

            if bill_dict.get('contact'):
                string += printer.text(bill_dict['contact']['name'] + new_line)
                string += new_line
                string += printer.text(bill_dict['contact']['street'] + ' ' + bill_dict['contact']['postcode'] + ' ' + bill_dict['contact']['city'])
                string += printer.text(bill_dict['contact']['state'] + ' ' + bill_dict['contact']['country'])
                string += new_line
                string += printer.text(_('VAT') + ':' + ' ' + bill_dict['contact']['vat_no'])
                string += new_line

            string += left_align
            string += printer.text(_('Bill No.') + ': ' + str(bill_dict['serial']))
            string += new_line
            string += printer.line(line_char_no=line_char_no)
            string += new_line

            white_spaces = [0.25, 0.20, 0.25, 0.25, 0.05]
            strings = [_('Price'), _('Quantity'), _('Discount'), '', _('Amount')]
            aligns = ['left', 'right', 'right', 'right', 'right']

            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=2)

            string += printer.line(line_char_no=line_char_no)

            for item in bill_dict['items']:

                string += item['name']
                string += new_line
                strings = [item['base'], item['quantity'], item['discount'], item['total'], item['tax_rate_id']]
                string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=2)
                string += new_line

            string += printer.line(line_char_no=line_char_no)
            string += new_line

            white_spaces = [0.5, 0.5]
            strings = [_('Total') + ' ' + bill_dict['currency'] + ':', bill_dict['total']]
            aligns = ['left', 'right']
            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)

            string += printer.line(line_char_no=line_char_no)
            string += new_line

            white_spaces = [0.08, 0.22, 0.23, 0.23, 0.24]
            strings = ['', _('Rate'), _('Subtotal'), _('Tax'), _('Total')]
            aligns = ['left', 'right', 'right', 'right', 'right']

            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)


            for rate in bill_dict['tax_rates']:
                strings = [rate['id'], rate['amount'], rate['net_sum'], rate['tax_sum'], rate['gross_sum']]
                string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)
                string += new_line


            string += printer.line(line_char_no=line_char_no, style='Dashed')

            strings = [_('Sum'), '', bill_dict['tax_sums']['net_sum'], bill_dict['tax_sums']['tax_sum'], bill_dict['tax_sums']['gross_sum']]
            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)

            string += new_line

            white_spaces = [0, 1]
            strings = [_('Cashier') + ': ' + bill_dict['user_name'], bill_dict['timestamp']]
            aligns = ['left', 'right']

            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)

            string += new_line
            string += new_line
            string += new_line
            return string
    return


#########
# views #
#########

@login_required
def create_bill(request, company):
    """ there's bill and items in request.POST['data'], create a new bill, and check all items and all """

    # get company
    try:
        c = Company.objects.get(url_name=company)
        return create_bill_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def create_bill_(request, c):
    def item_error(message, product):
        return JsonError(message + " " + _("(Item" + ": ") + product.name + ")")

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
        if existing_bill.status == g.PAID:
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

        'type': g.CASH,
        'status': g.WAITING,
        'items': [],
        'currency': get_company_value(request.user, c, 'pos_currency'),

        # numbers...
        'base': Decimal(0),
        'discount': Decimal(0),
        'tax': Decimal(0),
        'total': Decimal(0),

        'created_by': request.user
    }

    # timestamp
    try:
        # timestamp: send in an array of number:
        # [year, month, day, hour, minute, second]
        tn = [int(n) for n in data.get('timestamp')]
        bill['timestamp'] = dtm(year=tn[0],
                                month=tn[1],
                                day=tn[2],
                                hour=tn[3],
                                minute=tn[4],
                                second=tn[5])

    except (ValueError, TypeError):
        return JsonError(_("Invalid timestamp"))

    r = parse_decimal(request.user, c, data.get('total'))
    if not r['success'] or r['number'] <= Decimal('0'):
        return JsonError(_("Invalid grand total value"))
    else:
        bill['total'] = r['number']

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

            bill['base'] += item['batch']
            bill['discount'] += item['discount']
            bill['tax'] += item['tax']
        except ValueError as e:
            return item_error(e.message, product)

    # at this point, everything is fine, insert into database

    if existing_bill:
        existing_bill.delete()

    bill_payment = Payment(
        type=g.CASH,
        total=bill['total'],
        currency=get_company_value(request.user, c, 'pos_currency'),
        transaction_datetime=datetime.utcnow(),
        status=g.WAITING,
        created_by=request.user
    )
    bill_payment.save()

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
        #timestamp=dtm.utcnow().replace(tzinfo=timezone(get_company_value(request.user, c, 'pos_timezone'))),
        timestamp=bill['timestamp'],
        payment=bill_payment,

        base=bill['base'],
        discount=bill['discount'],
        tax=bill['tax']
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

    db_bill.save()

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
    unfinished_bills = Bill.objects.filter(company=c).exclude(payment__status=g.PAID).order_by('-timestamp')

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
    if bill.status == g.PAID:
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
        return check_bill_status_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def check_bill_status_(request, c, android=False):
    # there should be bill_id in request.POST
    try:
        bill_id = int(JsonParse(request.POST.get('data')).get('bill_id'))
        bill = Bill.objects.get(company=c, id=bill_id)
    except (Bill.DoesNotExist, ValueError, TypeError):
        return JsonError(_("Bill does not exist or data is invalid"))

    if not has_permission(request.user, c, 'bill', 'edit'):
        return JsonResponse({'status': 'no_permission', 'message': 'no_permission'})

    # LOL :) - not LOL, rok does not understand - omg, omg, se eno tako..
    """
    if settings.DEBUG:
        if random.randint(0, 9) > 0:
            return JsonOk(extra={'paid': 'true'})
        else:
            return JsonOk(extra={'paid': 'false'})
    """

    if bill.status == g.PAID:
        if android:
            return JsonOk(extra={'paid': 'true', 'print': esc_format(request.user, c, bill, bill.register.receipt_format, esc_commands=True)})
        else:
            return JsonOk(extra={'paid': 'true'})
    else:
        return JsonOk(extra={'paid': 'false'})


@login_required
def finish_bill(request, company):
    """
        find the bill, update its status and set payment type and reference
    """
    try:
        c = Company.objects.get(url_name=company)
        return finish_bill_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def finish_bill_(request, c, android=False):
    # this should be only called from web, when paying with cash or credit card

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
    if d.get('status') == g.PAID:
        # check payment type
        payment_type = d.get('payment_type')

        if payment_type not in g.PAYMENT_TYPE_VALUES:
            return JsonError(_("Payment type does not exist"))

        bill.status = g.PAID

        if payment_type == g.CASH or payment_type == g.CREDIT_CARD:
            bill.payment.type = payment_type
            # payment reference: if paid with bitcoin - btc address, if paid with cash, cash amount given
            # tole bols, da gre v payment_info, oz. bo kar moglo it, k zdej se je transaction_reference spremenil
            # (hehe spremenil, a stekas?:) ... se je spremenil v btc_transaction_reference in paypal_transaction_reference
            # bill.payment.transaction_reference = d.get('payment_reference')
    else:
        bill.status = g.CANCELED

    bill.payment.save()
    bill.save()

    # if print is requested, return html, otherwise the 'ok' response
    if d.get('print'):
        if android:
            return JsonResponse({'status': 'ok',
                                 'bill_payment': payment_to_dict(request.user, c, bill.payment),
                                 'print': esc_format(request.user, c, bill, bill.register.receipt_format, esc_commands=True)})
        else:
            return JsonResponse({'status': 'ok',
                                 # 'print': esc_format(request.user, c, bill, bill.register.receipt_format, esc_commands=True),
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


def esc_format(user, company, bill, format, line_char_no=48, esc_commands=False):

    if format == "Page":
        return 'full_page_format'
    elif format == "Thermal":
        string = ''
        if esc_commands:
            bill_dict = bill_to_dict(user, company, bill)
            printer = escpostext.EscposText()
            new_line = '\x0a'
            center_align =  '\x1b\x61\x01'
            left_align = '\x1b\x61\x00'
            # center / bold
            string += center_align
            string += printer.text(bill_dict.get('issuer').get('name'))
            string += new_line
            # center
            string += printer.text(bill_dict.get('issuer').get('street') + ' ' + bill_dict.get('issuer').get('postcode') + ' ' + bill_dict.get('issuer').get('city'))
            string += new_line
            string += printer.text(bill_dict['issuer']['state'] + ' ' + bill_dict['issuer']['country'])
            string += new_line

            string += printer.text(_('VAT') + ':' + ' ' + bill_dict['issuer']['vat_no'])
            string += new_line

            string += printer.text(bill_dict['register']['location'])

            string += new_line

            if bill_dict.get('contact'):
                string += printer.text(bill_dict['contact']['name'] + new_line)
                string += new_line
                string += printer.text(bill_dict['contact']['street'] + ' ' + bill_dict['contact']['postcode'] + ' ' + bill_dict['contact']['city'])
                string += printer.text(bill_dict['contact']['state'] + ' ' + bill_dict['contact']['country'])
                string += new_line
                string += printer.text(_('VAT') + ':' + ' ' + bill_dict['contact']['vat_no'])
                string += new_line

            string += left_align
            string += printer.text(_('Bill No.') + ': ' + str(bill_dict['serial']))
            string += new_line
            string += printer.line(line_char_no=line_char_no)
            string += new_line


            white_spaces = [0.25, 0.20, 0.25, 0.25, 0.05]
            strings = [_('Price'), _('Quantity'), _('Discount'), '', _('Amount')]
            aligns = ['left', 'right', 'right', 'right', 'right']

            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=2)

            string += printer.line(line_char_no=line_char_no)

            for item in bill_dict['items']:

                string += item['name']
                string += new_line
                strings = [item['base'], item['quantity'], item['discount'], item['total'], item['tax_rate_id']]
                string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=2)
                string += new_line

            string += printer.line(line_char_no=line_char_no)
            string += new_line


            white_spaces = [0.5, 0.5]
            strings = [_('Total') + ' ' + bill_dict['currency'] + ':', bill_dict['total']]
            aligns = ['left', 'right']
            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)


            string += printer.line(line_char_no=line_char_no)
            string += new_line

            white_spaces = [0.08, 0.22, 0.23, 0.23, 0.24]
            strings = ['', _('Rate'), _('Subtotal'), _('Tax'), _('Total')]
            aligns = ['left', 'right', 'right', 'right', 'right']

            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)


            for rate in bill_dict['tax_rates']:
                strings = [rate['id'], rate['amount'], rate['net_sum'], rate['tax_sum'], rate['gross_sum']]
                string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)
                string += new_line


            string += printer.line(line_char_no=line_char_no, style='Dashed')

            strings = [_('Sum'), '', bill_dict['tax_sums']['net_sum'], bill_dict['tax_sums']['tax_sum'], bill_dict['tax_sums']['gross_sum']]
            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)

            string += new_line

            white_spaces = [0, 1]
            strings = [_('Cashier') + ': ' + bill_dict['user_name'], bill_dict['timestamp']]
            aligns = ['left', 'right']

            string += printer.full_text_line(white_spaces, strings, line_char_no, aligns=aligns, left_offset=0)

            string += new_line
            string += new_line
            string += new_line
            return string
    return


@login_required
def get_payment_btc_info(request, company):
    """
        check if the bill has been paid and return the status
    """
    try:
        c = Company.objects.get(url_name=company)
        return get_payment_btc_info_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def get_payment_btc_info_(request, c):
    # there should be bill_id in request.POST
    try:
        bill_id = int(JsonParse(request.POST.get('data')).get('bill_id'))
        bill = Bill.objects.get(company=c, id=bill_id)
    except (Bill.DoesNotExist, ValueError, TypeError):
        return JsonError(_("Bill does not exist or data is invalid"))

    extra = {}

    if bill.company == c and has_permission(request.user, c, 'bill', 'edit'):
        if settings.DEBUG and 'tomaz' in globals():
            btc_address = "17VP9cu7K75MswYrh2Ue5Ua6Up4ZiMLpYw"
            btc_amount = 0.01
        else:
            btc_address = bill.payment.get_btc_address(c.id)
            btc_amount = bill.payment.get_btc_amount(request.user, c)

        if btc_address == "":
            return JsonResponse({'status': 'could_not_get_btc_address', 'message': 'could_not_get_btc_address'})
        if not btc_amount:
            return JsonResponse({'status': 'could_not_get_btc_amount', 'message': 'could_not_get_btc_amount'})

        extra['btc_address'] = btc_address
        extra['btc_amount'] = btc_amount
    else:
        return JsonResponse({'status': 'error', 'message': 'trying_to_compromise'})

    return JsonOk(extra=extra)


@login_required
def change_payment_type(request, company):
    """
        check if the bill has been paid and return the status
    """
    try:
        c = Company.objects.get(url_name=company)
        return change_payment_type_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def change_payment_type_(request, c):
    # there should be bill_id in request.POST
    try:
        bill_id = int(JsonParse(request.POST.get('data')).get('bill_id'))
        bill = Bill.objects.get(company=c, id=bill_id)
    except (Bill.DoesNotExist, ValueError, TypeError):
        return JsonError(_("Bill does not exist or data is invalid"))

    if bill.company == c and has_permission(request.user, c, 'bill', 'edit'):
        type = JsonParse(request.POST.get('data')).get('type')

        try:
            bill_payment = Payment.objects.get(id=bill.payment.id)
            if bill_payment.status == g.PAID:
                return JsonResponse({'status': 'error', 'message': 'bill_payment_already_paid'})

            if type not in g.PAYMENT_TYPE_VALUES:
                return JsonResponse({'status': 'error', 'message': 'invalid_payment_type'})

            bill_payment.type = type
            bill_payment.save()

        except Payment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'no_payment_for_bill'})

    else:
        return JsonResponse({'status': 'error', 'message': 'trying_to_compromise'})

    return JsonOk()

@login_required
def send_invoice(request, company):
    """
        sends paypal invoice to the customer
    """

    try:
        c = Company.objects.get(url_name=company)
        return send_invoice_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@login_required
def send_invoice_(request, c):

    data = JsonParse(request.POST.get('data'))

    # there should be bill_id in request.POST
    try:
        bill_id = int(data.get('bill_id'))
        bill = Bill.objects.get(company=c, id=bill_id)
    except (Bill.DoesNotExist, ValueError, TypeError):
        return JsonError(_("Bill does not exist or data is invalid"))

    if bill.company == c and has_permission(request.user, c, 'bill', 'edit'):
        company_paypal_address = get_company_value(request.user, c, 'pos_payment_paypal_address')
        if company_paypal_address == "":
            company_paypal_address = c.email

        if bill.status == g.PAID:
            return JsonResponse({'status': 'error', 'message': 'bill_payment_already_paid'})

        merchant_info = {
            'email': company_paypal_address,
            'address': {
                'line1': c.street,
                'city': c.city,
                'country_code': c.country,
                'state': "XX"
            },
        }

        if c.name and c.name != "":
            merchant_info['business_name'] = c.name

        if c.phone and c.phone != "":
            merchant_info['phone'] = c.phone

        if c.website and c.website != "":
            merchant_info['website'] = c.website

        if c.postcode and c.postcode != "":
            merchant_info['address']['postal_code'] = c.postcode

        if c.vat_no and c.vat_no != "":
            merchant_info['tax_id'] = c.vat_no

        customer_email = data.get('customer_email')

        try:
            validate_email(customer_email)
        except ValidationError:
            return JsonResponse({'status': 'error', 'message': 'invalid_customer_email'})

        billing_info = [
            {
                "email": customer_email
            }
        ]

        shipping_info = None
        items = []

        bill_datetime_format = g.DATE_FORMATS[get_company_value(request.user, c, 'pos_date_format')]['python']
        bill_datetime = bill.timestamp.strftime(bill_datetime_format) + " UTC"

        currency = get_company_value(request.user, c, 'pos_currency')

        bill_items = BillItem.objects.filter(bill=bill)
        for bi in bill_items:
            try:
                product = Product.objects.get(id=bi.product_id)
                item_data = {
                    'name': product.name,
                    'quantity': bi.quantity.quantize(Decimal('.001'), rounding=ROUND_UP),
                    'unit_price': {
                        'currency': currency,
                        'value': bi.base.quantize(Decimal('.01'), rounding=ROUND_UP)
                    },
                    'tax': {
                        'name': product.tax.name,
                        'percent': bi.tax_rate.quantize(Decimal('.001'), rounding=ROUND_UP)
                    },
                    'date': bill_datetime,
                }

                if product.description and product.description != "":
                    item_data['description'] = product.description

                if bi.discount and bi.discount is not None:
                    item_data['discount'] = bi.discount

                items.append(item_data)

            except Product.DoesNotExist:
                pass

        paypal = Paypal()

        if not paypal.create_invoice(invoice_id=bill.serial, merchant_info=merchant_info, billing_info=billing_info,
                              shipping_info=shipping_info, items=items, invoice_date=bill_datetime):
            return JsonResponse({'status': 'error', 'message': 'could_not_create_invoice'})

        payment = bill.payment
        payment.paypal_transaction_reference = paypal.response["id"]
        payment.save()

        if not paypal.send_invoice():
            return JsonResponse({'status': 'error', 'message': 'could_not_send_invoice'})

    else:
        return JsonResponse({'status': 'error', 'message': 'trying_to_compromise'})

    return JsonOk()
