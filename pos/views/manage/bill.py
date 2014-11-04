from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404, HttpResponseRedirect, JsonResponse
from config.functions import get_date_format, get_company_value

from pos.models import Company, Category, Product, Contact, Bill, BillItem
from pos.views.bill import bill_to_dict
from pos.views.util import JsonError, JsonParse, JsonOk,  \
    max_field_length, has_permission, no_permission_view, JsonStringify, parse_date

from common import globals as g


class BillSearchForm(forms.Form):
    # search bill by:
    issued_from = forms.CharField(max_length=10, required=False)
    issued_to = forms.CharField(max_length=20, required=False)
    item_code = forms.CharField(max_length=max_field_length(Product, 'code'), required=False)
    contact = forms.CharField(max_length=128, required=False)
    id = forms.IntegerField(min_value=1, required=False)
    # TODO: amount (from...to)

    def clean(self):
        d = self.cleaned_data
        if not d.get('issued_from') and not d.get('issued_to') and not \
            d.get('item_code') and not d.get('contact') and not d.get('id'):
            raise ValidationError(_("Please enter at least one search criteria"))
        else:
            return super(BillSearchForm, self).clean()


###
### views
###
@login_required
def list_bills(request, company):
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'bill', 'view'):
        return no_permission_view(request, c, _("You have no permission to view bills."))

    # if no search was made, display last N bills (below)
    N = 10
    bills = Bill.objects.none()

    # show the filter form
    if request.method == 'POST':
        form = BillSearchForm(request.POST)

        if form.is_valid():
            bills = Bill.objects.filter(company=c, status='Paid').order_by('-timestamp')

            # filter by whatever is in the form:
            # issue date: from
            t = form.cleaned_data.get('issued_from')
            if t:
                r = parse_date(request.user, c, t)
                if r['success']:
                    bills = bills.filter(timestamp__gte=r['date'])

            # issue date: to
            t = form.cleaned_data.get('issued_to')
            if t:
                r = parse_date(request.user, c, t)
                if r['success']:
                    bills = bills.filter(timestamp__lte=r['date'])

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
    else:
        form = BillSearchForm()
        bills = Bill.objects.filter(company=c).order_by('-timestamp')[:N]

    # format all bills manually
    bills = [bill_to_dict(request.user, c, b) for b in bills]

    # paginate stuff
    # paginator = Paginator(discounts, g.MISC['discounts_per_page'])
    #
    # page = request.GET.get('page')
    # try:
    #     discounts = paginator.page(page)
    # except PageNotAnInteger:
    #     discounts = paginator.page(1)
    # except EmptyPage:
    #     discounts = paginator.page(paginator.num_pages)

    context = {
        'company': c,
        'bills': bills,
        #'paginator': paginator,
        'filter_form': form,
        'title': _("Discounts"),
        'site_title': g.MISC['site_title'],
        'date_format_django': get_date_format(request.user, c, 'django'),
        'date_format_js': get_date_format(request.user, c, 'js'),
        #'results_display': results_display,
        'currency': get_company_value(request.user, c, 'pos_currency'),
    }

    return render(request, 'pos/manage/bills.html', context)