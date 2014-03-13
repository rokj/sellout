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

from pos.models import Company, Discount, ProductDiscount
from pos.views.util import error, JSON_response, JSON_error, \
                           has_permission, no_permission_view, \
                           format_number, format_date, parse_date, parse_decimal, \
                           max_field_length
from common import globals as g
from config.functions import get_date_format, get_value

from datetime import date
import re

def is_discount_active(d):
    today = date.today()
    
    valid = False
    
    if not d.start_date and not d.end_date:
        valid = True
    elif d.start_date and not d.end_date:
        if d.start_date <= today:
            valid = True
    elif not d.start_date and d.end_date:
        if d.end_date >= today:
            valid = True
    elif d.start_date and d.end_date:
        if d.start_date <= today and d.end_date >= today:
            valid = True
        
    return valid

def discount_to_dict(user, d):
    return {
        'id':d.id,
        'description':d.description,
        'code':d.code,
        'type':d.type,
        'amount':format_number(user, d.amount),
        'start_date':format_date(user, d.start_date),
        'end_date':format_date(user, d.end_date),
        'active':d.active,
    }

@login_required
def JSON_discounts(request, company, product_id=None):
    """ returns all available discounts for this company in a list of dictionaries
        (see discount_to_dict for dictionary format)
    """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # permissions
    if not has_permission(request.user, c, 'discount', 'list'):
        return JSON_error(_("You have no permission to view discounts"))

    discounts = Discount.objects.filter(company__url_name=company, active=True).order_by('code')
    
    ds = []
    for d in discounts:
        if is_discount_active(d):
            ds.append(discount_to_dict(request.user, d))
    
    # serialize
    return JSON_response(ds)

def validate_discount(data, user):
    """ validates data for discount
        data is a dictionary with keys equal to model fields
        returns a dictionary: {
        'success': True if all data is valid, else False
        'message': None if data is valid, else a message for ValidationError or JSON_error
        'data':'cleaned' data if data is valid, else None
    """
    
    def err(message):
        return {'success':False, 'message':message, 'data':None}
    
    # description: just trim length
    if 'description' in data:
        data['description'] = data['description'][:max_field_length(Discount, 'description')]
    
    # code: it must exist and must not be too long
    if 'code' not in data:
        return err(_("Code is required"))
    elif len(data['code']) > max_field_length(Discount, 'code'):
        return err(_("Code is too long (maximum length is %s)"%max_field_length(Discount, 'code')))
    
    # type: see if it's in g.DISCOUNT_TYPES (search the first fields of tuples)
    if data['type'] not in [x[0] for x in g.DISCOUNT_TYPES]:
        print g.DISCOUNT_TYPES
        return err(_("Wrong discount type"))
        
    # amount: parse number
    if 'amount' not in data:
        return err(_("Amount is required"))
    else:
        r = parse_decimal(user, data['amount'])
        if r['success']:
            data['amount'] = r['number']
        else:
            return err(_("Wrong number format for amount"))
    
    # start_date and end_date: parse date (none of them is mandatory)
    if len(data['start_date']) > 0: # date fields are never empty (None)
        r = parse_date(user, data['start_date'])
        if r['success']:
            data['start_date'] = r['date']
        else:
            return err(_("Wrong format for start date"))
    else:
        del data['start_date']

    if len(data['end_date']) > 0:
        r = parse_date(user, data['end_date'])
        if r['success']:
            data['end_date'] = r['date']
        else:
            return err(_("Wrong format for end date"))
    else:
        del data['end_date']
            
    # active: doesn't matter
    
    # ok
    return {'success':True, 'message':None, 'data':data}

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
    active = forms.BooleanField(initial=True, required=False)
    
    def clean(self):
        # use the same clean method as JSON
        r = validate_discount(self.cleaned_data, self.user)
        if not r['success']:
            raise forms.ValidationError(r['message'])
        else:
            return r['data']

class DiscountFilterForm(forms.Form):
    description = forms.CharField(required=False)    
    code = forms.CharField(required=False)
    start_date = forms.CharField(required=False, max_length=g.DATE['max_date_length'])
    end_date = forms.CharField(required=False, max_length=g.DATE['max_date_length'])
    active = forms.NullBooleanField(required=False)

@login_required
def list_discounts(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'discount', 'list'):
        return no_permission_view(request, c, _("view discounts"))
    
    discounts = Discount.objects.filter(company__id=c.id)
    
    # show the filter form
    if request.method == 'POST':
        form = DiscountFilterForm(request.POST)
        
        if form.is_valid():
            # filter by whatever is in the form: description
            if form.cleaned_data.get('description'):
                discounts = discounts.filter(description__icontains=form.cleaned_data['description'])
            
            # code
            if form.cleaned_data.get('code'):
                discounts = discounts.filter(code__icontains=form.cleaned_data['code'])
            
            # start_date
            if form.cleaned_data.get('start_date'):
                # parse date first
                r = parse_date(request.user, form.cleaned_data.get('start_date'))
                if r['success']:
                    discounts = discounts.filter(start_date__gte=r['date'])
            
            # end_date
            if form.cleaned_data.get('end_date'):
                r = parse_date(request.user, form.cleaned_data.get('end_date'))
                if r['success']:
                    discounts = discounts.filter(start_date__gte=r['date'])
            
            # active
            if form.cleaned_data.get('active') is not None:
                discounts = discounts.filter(active=form.cleaned_data['active'])
                
            results_display = True # search results are being displayed
    else:
        form = DiscountFilterForm()
        results_display = False # no results are being displayed, so don't show the 'clear results' link in template
        
    # show discounts
    paginator = Paginator(discounts, get_value(request.user, 'pos_discounts_per_page'))

    page = request.GET.get('page')
    try:
        discounts = paginator.page(page)
    except PageNotAnInteger:
        discounts = paginator.page(1)
    except EmptyPage:
        discounts = paginator.page(paginator.num_pages)

    context = {
        'company':c,
        'discounts':discounts,
        'paginator':paginator,
        'filter_form':form,
        'title':_("Discounts"),
        'site_title':g.MISC['site_title'],
        'date_format_django':get_date_format(request.user, 'django'),
        'date_format_jquery':get_date_format(request.user, 'jquery'),
        'results_display':results_display,
    }

    return render(request, 'pos/manage/discounts.html', context) 

@login_required
def add_discount(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return no_permission_view(request, c, _("add discounts"))
    
    context = {
        'title':_("Add discount"),
        'site_title':g.MISC['site_title'],
        'company':c,
        'date_format_jquery':get_date_format(request.user, 'jquery'),
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
                description = form.cleaned_data.get('description'),
                code = form.cleaned_data.get('code'),
                type = form.cleaned_data.get('type'),
                amount = form.cleaned_data.get('amount'),
                start_date = form.cleaned_data.get('start_date'),
                end_date = form.cleaned_data.get('end_date'),
                active = form.cleaned_data.get('active'),
                
                created_by = request.user,
                company = c
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
        'company':c,
        'discount_id':discount_id,
        'date_format_jquery':get_date_format(request.user, 'jquery'),
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
        form = DiscountForm(request.POST, initial=discount_to_dict(request.user, discount))
        form.company = c
        form.user = request.user
        
        if form.is_valid():
            discount.description = form.cleaned_data.get('description')
            discount.code = form.cleaned_data.get('code')
            discount.type = form.cleaned_data.get('type')
            discount.amount = form.cleaned_data.get('amount')
            discount.start_date = form.cleaned_data.get('start_date')
            discount.end_date = form.cleaned_data.get('end_date')
            discount.active = form.cleaned_data.get('active')
            discount.save()
            
            return redirect('pos:list_discounts', company=c.url_name)
    else:
        form = DiscountForm(initial=discount_to_dict(request.user, discount))
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
        return error(_("You have no permission to delete discounts."))
    
    discount.delete()
    
    return redirect('pos:list_discounts', company=c.url_name)


def get_all_discounts(user, company):
    discounts = Discount.objects.filter(company=company)

    r = []
    for d in discounts:
        r.append(discount_to_dict(user, d))

    return r