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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Company, Bill, BillItem, Product
from pos.views.bill import create_bill, finish_bill
from pos.views.util import has_permission, JsonResponse, JsonParse, JsonError, \
    format_number, parse_decimal, format_date, format_time
from config.functions import get_company_value
import common.globals as g

from pytz import timezone
from datetime import datetime as dtm
from decimal import Decimal


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
    i['quantity'] = format_number(user, company, item.quantity)
    i['base_price'] = format_number(user, company, item.base_price)
    i['tax_percent'] = format_number(user, company, item.tax_percent)
    i['tax_absolute'] = format_number(user, company, item.tax_absolute)
    i['discount_absolute'] = format_number(user, company, item.discount_absolute)
    i['single_total'] = format_number(user, company, item.single_total)
    i['total'] = format_number(user, company, item.total)
    i['bill_notes'] = item.bill_notes

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
    b['bill_id'] = bill.id
    b['till'] = bill.till
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



def validate_bill_item(data):
    """ TODO: finds bill and item in database and """
    pass


#########
# views #
#########
@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_create_bill(request, company):
    return create_bill(request, company)
    # return JsonOk()


@login_required
def get_active_bill(request, company):
    """ returns the last edited (active) bill if any, or an empty one """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))
    
    # check permissions
    if not has_permission(request.user, c, 'bill', 'list'):
        return JsonError(_("You have no permission to view bills"))
    
    try:
        bill = Bill.objects.get(company=c, user=request.user, status="Active")
    except Bill.DoesNotExist:
        # if there's no active bill, start a new one
        return JsonResponse(new_bill(request.user, c))
    except Bill.MultipleObjectsReturned:
        # two active bills (that shouldn't happen at all)
        return JsonError(_("Multiple active bills found"))
        
    # serialize the fetched bill and return it
    bill = bill_to_dict(request.user, c, bill)
    return JsonResponse({'status': 'ok', 'bill': bill})



@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_finish_bill(request, company):
    return finish_bill(request, company)
    # return JsonOk()