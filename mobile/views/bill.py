#
# Bill
#   ajax views:
#     get_active_bill: finds an unfinished bill and returns it (returns a new bill if none was found)
#     add_item: adds an item to bill
#     edit_item: edits an existing item
#     delete_item
#
from common.decorators import login_required
from django.utils.translation import ugettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Company, Bill, BillItem, Product
from pos.views.bill import create_bill, finish_bill, finish_bill_, create_bill_, get_payment_btc_info_, \
    check_bill_status_, change_payment_type_, send_invoice_
from common.functions import has_permission, JsonResponse, JsonParse, JsonError, \
    format_number, parse_decimal, format_date, format_time
from config.functions import get_company_value
import common.globals as g

from pytz import timezone
from datetime import datetime as dtm
from decimal import Decimal


#########
# views #
#########
@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_create_bill(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return create_bill_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))
    # return JsonOk()


@login_required
def get_active_bill(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))
    
    # check permissions
    if not has_permission(request.user, c, 'bill', 'list'):
        return JsonError(_("You have no permission to view bills"))
    
    try:
        bill = Bill.objects.get(company=c, user=request.user, status="Active")
    except Bill.DoesNotExist:
        return
        # if there's no active bill, start a new one
        # return JsonResponse(new_bill(request.user, c))
    except Bill.MultipleObjectsReturned:
        # two active bills (that shouldn't happen at all)
        return JsonError(_("Multiple active bills found"))
        
    # serialize the fetched bill and return it
    #bill = bill_to_dict(request.user, c, bill)
    return JsonResponse({'status': 'ok', 'bill': bill})


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_finish_bill(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return finish_bill_(request, c, android=True)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))
    # return JsonOk()


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def get_payment_btc_info(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return get_payment_btc_info_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def check_bill_status(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return check_bill_status_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def change_payment_type(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return change_payment_type_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def send_invoice(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
        return send_invoice_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))
