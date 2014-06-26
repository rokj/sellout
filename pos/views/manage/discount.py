# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: discounts

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from pos.models import Company, Discount
from pos.views.util import error, JSON_response, JSON_error, \
                           has_permission, no_permission_view, \
                           format_number, format_date, parse_date, parse_decimal, \
                           max_field_length
from common import globals as g
from config.functions import get_date_format, get_user_value, get_company_value


def discount_to_dict(user, company, d, android=False):
    ret = {
        'id': d.id,
        'description': d.description,
        'code': d.code,
        'type': d.type,
        'amount': format_number(user, company, d.amount),
        'enabled': d.enabled,
        'active': d.is_active,
    }

    if android and d.start_date:
        ret['start_date'] = [d.start_date.year, d.start_date.month, d.start_date.day]
    else:
        ret['start_date'] = format_date(user, company, d.start_date)

    if android and d.end_date:
        ret['end_date'] = [d.end_date.year, d.end_date.month, d.end_date.day]
    else:
        ret['end_date'] = format_date(user, company, d.end_date)
    return ret


@login_required
def JSON_discounts(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'discount', 'list'):
        return JSON_error(_("You have no permission to view discounts"))

    return JSON_response(get_all_discounts(request.user, c))


def get_all_discounts(user, company, android=False):
    """ returns all available discounts for this company in a list of dictionaries
        (see discount_to_dict for dictionary format)
    """
    discounts = Discount.objects.filter(company=company, enabled=True).order_by('code')

    ds = []
    for d in discounts:
        if d.is_active:
            ds.append(discount_to_dict(user, company, d, android))

    return ds


def validate_discount(data, user, company):
    """ validates data for discount
        data is a dictionary with keys equal to model fields
        returns a dictionary: {
        'success': True if all data is valid, else False
        'message': None if data is valid, else a message for ValidationError or JSON_error
        'data':'cleaned' data if data is valid, else None
    """
    
    def err(message):
        return {'success': False, 'message': message, 'data': None}
    
    # description: just trim length
    if 'description' in data:
        data['description'] = data['description'][:max_field_length(Discount, 'description')]
    
    # code: it must exist and must not be too long
    if 'code' not in data:
        return err(_("Code is required"))
    elif len(data['code']) > max_field_length(Discount, 'code'):
        return err(_("Code is too long (maximum length is %s)" % max_field_length(Discount, 'code')))
    
    # type: see if it's in g.DISCOUNT_TYPES (search the first fields of tuples)
    if data['type'] not in [x[0] for x in g.DISCOUNT_TYPES]:
        print g.DISCOUNT_TYPES
        return err(_("Wrong discount type"))
        
    # amount: parse number
    if 'amount' not in data:
        return err(_("Amount is required"))
    else:
        r = parse_decimal(user, company, data['amount'])
        if r['success']:
            data['amount'] = r['number']
        else:
            return err(_("Wrong number format for amount"))
    
    # start_date and end_date: parse date (none of them is mandatory)
    if len(data['start_date']) > 0: # date fields are never empty (None)
        r = parse_date(user, company, data['start_date'])
        if r['success']:
            data['start_date'] = r['date']
        else:
            return err(_("Wrong format for start date"))
    else:
        del data['start_date']

    if len(data['end_date']) > 0:
        r = parse_date(user, company, data['end_date'])
        if r['success']:
            data['end_date'] = r['date']
        else:
            return err(_("Wrong format for end date"))
    else:
        del data['end_date']
            
    # enabled: doesn't matter
    
    # ok
    return {'success': True, 'message': None, 'data': data}


#############
### views ###
#############
class DiscountForm(forms.Form):
    description = forms.CharField(required=False, widget=forms.Textarea, max_length=max_field_length(Discount, 'description'))
    code = forms.CharField(required=True, max_length=max_field_length(Discount, 'code'))
    type = forms.ChoiceField(choices=g.DISCOUNT_TYPES, required=True)
    # this should be decimal, but we're formatting it our way
    amount = forms.CharField(max_length=g.DECIMAL['percentage_decimal_places'] + 4, required=True)
    # this should be date...
    start_date = forms.CharField(g.DATE['max_date_length'], required=False)
    end_date = forms.CharField(g.DATE['max_date_length'], required=False)
    enabled = forms.BooleanField(initial=True, required=False)
    
    def clean(self):
        # use the same clean method as JSON
        r = validate_discount(self.cleaned_data, self.user, self.company)
        if not r['success']:
            raise forms.ValidationError(r['message'])
        else:
            return r['data']


class DiscountFilterForm(forms.Form):
    search = forms.CharField(label=_("Search text"), required=False)
    start_date = forms.CharField(required=False, max_length=g.DATE['max_date_length'])
    end_date = forms.CharField(required=False, max_length=g.DATE['max_date_length'])
    enabled = forms.NullBooleanField(required=False)


@login_required
def list_discounts(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'discount', 'list'):
        return no_permission_view(request, c, _("view discounts"))
    
    discounts = Discount.objects.filter(company__id=c.id)

    results_display = False

    # show the filter form
    if request.method == 'POST':
        form = DiscountFilterForm(request.POST)
        
        if form.is_valid():
            # filter by whatever is in the form: description
            if form.cleaned_data.get('search'):
                discounts = discounts.filter(description__icontains=form.cleaned_data['search']) | \
                            discounts.filter(code__icontains=form.cleaned_data['search'])
            
            # start_date
            if form.cleaned_data.get('start_date'):
                # parse date first
                r = parse_date(request.user, c, form.cleaned_data.get('start_date'))
                if r['success']:
                    discounts = discounts.filter(start_date__gte=r['date'])
            
            # end_date
            if form.cleaned_data.get('end_date'):
                r = parse_date(request.user, c, form.cleaned_data.get('end_date'))
                if r['success']:
                    discounts = discounts.filter(start_date__gte=r['date'])
            
            # enabled
            if form.cleaned_data.get('enabled') is not None:
                discounts = discounts.filter(active=form.cleaned_data['enabled'])
                
            results_display = True  # search results are being displayed
    else:
        form = DiscountFilterForm()

    # show discounts
    paginator = Paginator(discounts, get_user_value(request.user, 'pos_discounts_per_page'))

    page = request.GET.get('page')
    try:
        discounts = paginator.page(page)
    except PageNotAnInteger:
        discounts = paginator.page(1)
    except EmptyPage:
        discounts = paginator.page(paginator.num_pages)

    context = {
        'company': c,
        'discounts': discounts,
        'paginator': paginator,
        'filter_form': form,
        'title': _("Discounts"),
        'site_title': g.MISC['site_title'],
        'date_format_django': get_date_format(request.user, c, 'django'),
        'date_format_js': get_date_format(request.user, c, 'js'),
        'results_display': results_display,
        'currency': get_company_value(request.user, c, 'pos_currency'),
    }

    return render(request, 'pos/manage/discounts.html', context) 

@login_required
def add_discount(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return no_permission_view(request, c, _("add discounts"))
    
    context = {
        'title': _("Add discount"),
        'site_title': g.MISC['site_title'],
        'company': c,
        'date_format_js': get_date_format(request.user, c, 'js'),
    }
    
    # check for permission for adding discounts
    if not request.user.has_perm('pos.add_discount'):
        return error(request, _("You have no permission to add discounts."))

    if request.method == 'POST':
        # submit data
        form = DiscountForm(request.POST)
        form.company = c
        form.user = request.user
        
        if form.is_valid():
            # save the new discount and redirect back to discounts
            d = Discount(
                description=form.cleaned_data.get('description'),
                code=form.cleaned_data.get('code'),
                type=form.cleaned_data.get('type'),
                amount=form.cleaned_data.get('amount'),
                start_date=form.cleaned_data.get('start_date'),
                end_date=form.cleaned_data.get('end_date'),
                enabled=form.cleaned_data.get('enabled'),
                
                created_by=request.user,
                company=c
            )
            d.save()
            
            return redirect('pos:list_discounts', company=c.url_name)
    else:
        form = DiscountForm()
        form.company = c
        form.user = request.user
        
    context['form'] = form
    context['company'] = c
    context['add'] = True
    
    return render(request, 'pos/manage/discount.html', context)

@login_required
def edit_discount(request, company, discount_id):
    # edit an existing contact
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return no_permission_view(request, c, _("edit discounts"))
    
    context = {
        'company': c,
        'discount_id': discount_id,
        'date_format_js': get_date_format(request.user, c, 'js'),
    }
    
    discount = get_object_or_404(Discount, id=discount_id)
        
    # check if contact actually belongs to the given company
    if discount.company != c:
        raise Http404
        
    # check if user has permissions to change contacts
    if not request.user.has_perm('pos.change_discount'):
        return error(request, _("You have no permission to edit discounts."))

    if request.method == 'POST':
        # submit data
        form = DiscountForm(request.POST, initial=discount_to_dict(request.user, c, discount))
        form.company = c
        form.user = request.user
        
        if form.is_valid():
            discount.description = form.cleaned_data.get('description')
            discount.code = form.cleaned_data.get('code')
            discount.type = form.cleaned_data.get('type')
            discount.amount = form.cleaned_data.get('amount')
            discount.start_date = form.cleaned_data.get('start_date')
            discount.end_date = form.cleaned_data.get('end_date')
            discount.enabled = form.cleaned_data.get('enabled')
            discount.save()
            
            return redirect('pos:list_discounts', company=c.url_name)
    else:
        form = DiscountForm(initial=discount_to_dict(request.user, c, discount))
        form.company = c
        form.user = request.user
        
    context['form'] = form
    
    return render(request, 'pos/manage/discount.html', context)

@login_required
def delete_discount(request, company, discount_id):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return no_permission_view(request, c, _("delete discounts"))
    
    discount = get_object_or_404(Discount, id=discount_id)
    
    if discount.company != c:
        raise Http404
    
    if not request.user.has_perm('pos.delete_discount'):
        return error(request, _("You have no permission to delete discounts."))
    
    discount.delete()
    
    return redirect('pos:list_discounts', company=c.url_name)

