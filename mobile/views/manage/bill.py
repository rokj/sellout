from django.utils.translation import ugettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Company, Bill, BillItem
from pos.views.bill import bill_to_dict, create_printable_bill
from common.functions import has_permission, JsonError, JsonParse, JsonOk

import datetime as dtm

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def list_bills(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'bill', 'view'):
        return JsonError(_("You have no permission to view bills."))

    N = 10  # if no search was made, display last N bills (below)
    searched = False

    data = JsonParse(request.POST['data'])

    if data.get('search'):
        # decide which way to order the results
        # this is the fake switch statement that is missing in python for no obvious reason
        ordering = {
            'id': 'serial',
            'date': 'timestamp',
            'amount': 'total'
        }
        order = ordering.get(data.get('sort_by'))
        if data.get('sort_order') == 'desc':
            order = '-' + order

        bills = Bill.objects.filter(company=c, status='Paid').order_by(order)

        # filter by whatever is in the form:
        # issue date: from
        issued_from = data.get('issued_from')
        if issued_from:
            t = dtm.date(year=issued_from[0], month=issued_from[1],
                                 day=issued_from[2])
            bills = bills.filter(timestamp__gte=t)

        # issue date: to
        issued_to = data.get('issued_to')
        if issued_to:
            t = dtm.date(year=issued_to[0], month=issued_to[1],
                                 day=issued_to[2])
            bills = bills.filter(timestamp__lte=t)

        # item:
        t = data.get('item_code')
        if t:
            ids = [i.id for i in BillItem.objects.only('bill_id').filter(code__icontains=t)]

            # find all bills that include item that contains this code
            bills = bills.filter(id__in=ids)

        # contact
        t = data.get('contact')
        if t:
            bills = bills.filter(contact__first_name__icontains=t) | \
                    bills.filter(contact__last_name__icontains=t) | \
                    bills.filter(contact__company_name__icontains=t)


        # bill number
        t = data.get('id')
        if t:
            bills = bills.filter(serial=t)

        # amount: from
        t = data.get('amount_from')
        if t:
            bills = bills.filter(total__gte=t)

        # amount: to
        t = data.get('amount_to')
        if t:
            bills = bills.filter(total__lte=t)

        # user
        t = data.get('user_name')
        if t:
            bills = bills.filter(user_name__icontains=t)

        page = data.get('page')
        searched = True
    else:
        bills = Bill.objects.filter(company=c, status='Paid').order_by('-timestamp')[:N]

    # format all bills manually
    bills = [bill_to_dict(request.user, c, b) for b in bills]

    return JsonOk(extra=bills)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def print_bill(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'bill', 'view'):
        return JsonError(_("You have no permission to view bills."))

    data = JsonParse(request.POST['data'])

    bill_id = data.get('id')

    if bill_id:
        try:
            b = Bill.objects.get(company=c, serial=bill_id)
            bill = create_printable_bill(request.user, c, b, esc=True)
        except Bill.DoesNotExist:
            return JsonError(_("Bill does not exist"))


    return JsonOk(extra=bill)
