from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from common.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from common.globals import PAID
from config.functions import get_date_format, get_company_value

from pos.models import Company, Product, Bill, BillItem
from pos.views.bill import bill_to_dict
from common.functions import max_field_length, has_permission, no_permission_view, \
    CompanyUserForm, CustomDateField, CustomDecimalField

from common import globals as g


class BillSearchForm(CompanyUserForm):
    payment_status_choices = [('', _("Any"))] + list(g.BILL_STATUS)

    # search bill by:
    issued_from = CustomDateField(max_length=10, required=False)
    issued_to = CustomDateField(max_length=20, required=False)
    item_code = forms.CharField(max_length=max_field_length(Product, 'code'), required=False)
    contact = forms.CharField(max_length=128, required=False)
    serial = forms.CharField(required=False)
    status = forms.ChoiceField(choices=payment_status_choices, required=False, initial=PAID)
    amount_from = CustomDecimalField(max_length=g.DECIMAL['currency_digits'], required=False)
    amount_to = CustomDecimalField(max_length=g.DECIMAL['currency_digits'], required=False)
    user_name = forms.CharField(max_length=128, required=False)

    sort_by = forms.ChoiceField(choices=(("serial", _("Number")), ("date", _("Date")), ("amount", _("Amount")),))
    sort_order = forms.ChoiceField(choices=(("desc", _("Descending")), ("asc", _("Ascending")),))

    page = forms.IntegerField(required=False, widget=forms.HiddenInput)


###
### views
###
@login_required
def list_bills(request, company):
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'bill', 'view'):
        return no_permission_view(request, c, _("You have no permission to view bills."))

    N = 10  # if no search was made, display last N bills (below)
    searched = False

    # use GET for everything: there's little parameters and when using POST, paginator gets
    # in the way with GET requests
    form = BillSearchForm(data=request.GET, user=request.user, company=c)

    if form.is_valid():
        # decide which way to order the results
        # this is the fake switch statement that is missing in python for no obvious reason
        ordering = {
            'serial': 'serial',
            'date': 'timestamp',
            'amount': 'total'
        }
        order = ordering.get(form.cleaned_data.get('sort_by'))
        if form.cleaned_data.get('sort_order') == 'desc':
            order = '-' + order

        bills = Bill.objects.filter(company=c).order_by(order)

        # filter by whatever is in the form:
        # issue date: from
        t = form.cleaned_data.get('issued_from')
        if t:
            bills = bills.filter(timestamp__gte=t)

        # issue date: to
        t = form.cleaned_data.get('issued_to')
        if t:
            bills = bills.filter(timestamp__lte=t)

        # item:
        t = form.cleaned_data.get('item_code')
        if t:
            ids = [i.id for i in BillItem.objects.only('bill_id').filter(code__icontains=t)]

            # find all bills that include item that contains this code
            bills = bills.filter(id__in=ids)

        # contact
        t = form.cleaned_data.get('contact')
        if t:
            bills = bills.filter(contact__first_name__icontains=t) | \
                    bills.filter(contact__last_name__icontains=t) | \
                    bills.filter(contact__company_name__icontains=t)

        # bill number
        t = form.cleaned_data.get('serial')
        print t
        if t:
            bills = bills.filter(formatted_serial__icontains=t)

        # status
        t = form.cleaned_data.get('status')
        if t:
            bills = bills.filter(payment__status=t)

        # amount: from
        t = form.cleaned_data.get('amount_from')
        if t:
            bills = bills.filter(total__gte=t)

        # amount: to
        t = form.cleaned_data.get('amount_to')
        if t:
            bills = bills.filter(total__lte=t)

        # user
        t = form.cleaned_data.get('user_name')
        if t:
            bills = bills.filter(user_name__icontains=t)

        page = form.cleaned_data.get('page')
        searched = True
    else:
        form = BillSearchForm(data=None, user=request.user, company=c)
        page = 1

        bills = Bill.objects.filter(company=c).order_by('-timestamp')[:N]

    # format all bills manually
    bills = [bill_to_dict(request.user, c, b) for b in bills]

    paginator = Paginator(bills, g.MISC['bills_per_page'])
    if page:
        bills = paginator.page(page)
    else:
        bills = paginator.page(1)

    context = {
        'company': c,

        'bills': bills,
        'searched': searched,

        'filter_form': form,

        'title': _("Bills"),
        'site_title': g.MISC['site_title'],
        'date_format_django': get_date_format(request.user, c, 'django'),
        'date_format_js': get_date_format(request.user, c, 'js'),
        'currency': get_company_value(request.user, c, 'pos_currency'),
    }

    return render(request, 'pos/manage/bills.html', context)