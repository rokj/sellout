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
                           format_number, format_date, parse_decimal
from common import globals as g
from config.functions import get_date_format, get_value

from datetime import date

def is_discount_valid(d):
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
    # send all available discounts for this company
    # available:
    #  - active = True
    #  - valid date
    # valid dates: 
    #  - if no dates entered
    #  - only start date: it must be before today
    #  - only end date: it must be after today
    #  - both start and end date: today must be between them
    # (see discount_to_dict)
    
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # permissions
    

    discounts = Discount.objects.filter(company__url_name=company, active=True)
    
    # put discounts in a dictionary[key=id] for easier searching and handling
    ds = {}
    
    for d in discounts:
        if is_discount_valid(d):
            ds[d.id] = discount_to_dict(request.user, d)
    
    # serialize
    return JSON_response(ds)

#############
### views ###
#############
class DiscountForm(forms.ModelForm):
    user = None
    company = None
    
    # override amount and date fields for custom field formatting
    # when initializing DiscountForm, a 'user' parameter is required
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs['user']
            # if 'user' is passed to the original __init__ function, it will complain
            del kwargs['user']
        
        super(DiscountForm, self).__init__(*args, **kwargs)
        
        if self.user:
            if 'amount' in self.initial:
                self.initial['amount'] = format_number(self.user, self.initial['amount'])
            if 'start_date' in self.initial:
                self.initial['start_date'] = format_date(self.user, self.initial['start_date'])
            if 'end_date' in self.initial:
                self.initial['end_date'] = format_date(self.user, self.initial['end_date'])

    # override the amount widget with plain text and clean manually;
    # this is to support arbitrary decimal separators
    amount = forms.CharField(max_length = g.DECIMAL['currency_digits'])
    
    def clean_amount(self):
        r = parse_decimal(self.user, self.cleaned_data['amount'])
        if not r['success']:
            raise forms.ValidationError(_("Check amount"))
        else:
            return r['number']
    
    def clean_code(self):
        code = self.cleaned_data['code']
        
        if 'code' in self.initial:
            # this discount is being edited
            if code == self.initial['code']:
                # and code hasn't been changed
                return code 
        
        if Discount.objects.filter(company=self.company, code=code).exists():
            raise forms.ValidationError(_("A discount with this code already exists"))
        else:
            return code
    
    class Meta:
        # override the decimal field for custom decimal separator
        amount = forms.CharField()
        
        model = Discount
        fields = ['description',
                  'code',
                  'type',
                  'amount',
                  'start_date',
                  'end_date',
                  'active']

class DiscountFilterForm(forms.Form):
    description = forms.CharField(required=False)    
    code = forms.CharField(required=False)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    active = forms.NullBooleanField(required=False)

    # custom display of 'custom-formatted' fields: see __init__ for DiscountForm    
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs['user']
            del kwargs['user']
        
        super(DiscountFilterForm, self).__init__(*args, **kwargs)
        
        if self.user:
            if 'start_date' in self.initial:
                self.initial['start_date'] = format_date(self.user, self.initial['start_date'])
            if 'end_date' in self.initial:
                self.initial['end_date'] = format_date(self.user, self.initial['end_date'])

@login_required
def list_discounts(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'discount', 'list'):
        return no_permission_view(request, c, _("view discounts"))
    
    discounts = Discount.objects.filter(company__id=c.id)
    
    # show the filter form
    if request.method == 'POST':
        form = DiscountFilterForm(request.POST, user=request.user)
        
        if form.is_valid():
            # filter by whatever is in the form: description
            if form.cleaned_data.get('description'):
                discounts = discounts.filter(description__icontains=form.cleaned_data['description'])
            
            # code
            if form.cleaned_data.get('code'):
                discounts = discounts.filter(code__icontains=form.cleaned_data['code'])
            
            # start_date
            if form.cleaned_data.get('start_date'):
                discounts = discounts.filter(start_date__gte=form.cleaned_data['start_date'])
            
            # end_date
            if form.cleaned_data.get('end_date'):
                discounts = discounts.filter(end_date__lte=form.cleaned_data['end_date'])
            
            # active
            if form.cleaned_data.get('active') is not None:
                discounts = discounts.filter(active=form.cleaned_data['active'])
                
            results_display = True # search results are being displayed
            
    else:
        form = DiscountFilterForm(user=request.user)
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
        form = DiscountForm(request.POST, user=request.user)
        form.company = c
        
        if form.is_valid():
            discount = form.save(False)
            # created_by and company_id
            if 'created_by' not in form.cleaned_data:
                discount.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                discount.company_id = c.id
        
            form.save()
            
            return redirect('pos:list_discounts', company=c.url_name)
    else:
        form = DiscountForm(user=request.user)
        form.company = c
        
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
        form = DiscountForm(request.POST, instance=discount, user=request.user)
        form.company = c
        
        if form.is_valid():
            # created_by and company_id
            discount = form.save(False)
            if 'created_by' not in form.cleaned_data:
                discount.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                discount.company_id = c.id
        
            form.save()
            
            return redirect('pos:list_discounts', company=c.url_name)
    else:
        form = DiscountForm(user=request.user, instance=discount)
        form.company = c
        
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
