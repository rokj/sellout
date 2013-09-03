# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: discounts

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from pos.models import Company, Category, Contact, Discount, Product, Price
from pos.views.util import error, JSON_response, JSON_parse, resize_image, validate_image
from common import globals as g
from common import unidecode
from common.functions import get_random_string

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

def discount_to_dict(d):
    return {
        'id':d.id,
        'description':d.description,
        'code':d.code,
        'type':d.type,
        'amount':str(d.amount),
        #'start_date':d.start_date, # TODO: format date
        #'end_date':d.end_date,
        'active':d.active,
    }
    
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

    discounts = Discount.objects.filter(company__url_name=company, active=True)
    
    # put discounts in a dictionary[key=id] for easier searching and handling
    ds = {}
    
    for d in discounts:
        if is_discount_valid(d):
            ds[d.id] = discount_to_dict(d)
    
    # serialize
    return JSON_response(ds)

#############
### views ###
#############
class DiscountForm(forms.ModelForm):
    class Meta:
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

def list_discounts(request, company):
    company = get_object_or_404(Company, url_name=company)
    
    discounts = Discount.objects.filter(company__id=company.id)
    
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
                discounts = discounts.filter(start_date__gte=form.cleaned_data['start_date'])
            
            # end_date
            if form.cleaned_data.get('end_date'):
                discounts = discounts.filter(end_date__lte=form.cleaned_data['end_date'])
            
            # active
            if form.cleaned_data.get('active') is not None:
                discounts = discounts.filter(active=form.cleaned_data['active'])
            
    else:
        form = DiscountFilterForm()
        
    # show contacts
    paginator = Paginator(discounts, g.MISC['discounts_per_page'])

    page = request.GET.get('page')
    try:
        discounts = paginator.page(page)
    except PageNotAnInteger:
        discounts = paginator.page(1)
    except EmptyPage:
        discounts = paginator.page(paginator.num_pages)

    context = {
        'company':company,
        'discounts':discounts,
        'paginator':paginator,
        'filter_form':form,
    }

    return render(request, 'pos/manage/discounts.html', context) 

def add_discount(request, company):
    company = get_object_or_404(Company, url_name=company)
    context = {}
    context['company'] = company.url_name
    
    # check for permission for adding discounts
    if not request.user.has_perm('pos.add_discount'):
        return error(request, _("You have no permission to add discounts."))

    if request.method == 'POST':
        # submit data
        form = DiscountForm(request.POST)
        
        if form.is_valid():
            # created_by and company_id
            contact = form.save(False)
            if 'created_by' not in form.cleaned_data:
                contact.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                contact.company_id = company.id
        
            form.save()
            
            return redirect('pos:list_discounts', company=company.url_name)
    else:
        form = DiscountForm()
        
    context['form'] = form
    context['company'] = company
    context['add'] = True
    
    return render(request, 'pos/manage/discount.html', context)


def edit_discount(request, company, discount_id):
    # edit an existing contact
    company = get_object_or_404(Company, url_name=company)
    context = {}
    context['company'] = company
    context['discount_id'] = discount_id
    
    discount = get_object_or_404(Discount, id=discount_id)
        
    # check if contact actually belongs to the given company
    if discount.company != company:
        raise Http404
        
        # check if user has permissions to change contacts
        if not request.user.has_perm('pos.change_discount'):
            return error(request, _("You have no permission to edit discounts."))

    if request.method == 'POST':
        # submit data
        form = DiscountForm(request.POST, instance=discount)
        
        if form.is_valid():
            # created_by and company_id
            discount = form.save(False)
            if 'created_by' not in form.cleaned_data:
                discount.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                discount.company_id = company.id
        
            form.save()
            
            return redirect('pos:list_discounts', company=company.url_name)
    else:
        form = DiscountForm(instance=discount)
        
    context['form'] = form
    
    return render(request, 'pos/manage/discount.html', context)

def delete_discount(request, company, discount_id):
    company = get_object_or_404(Company, url_name=company)
    discount = get_object_or_404(Discount, id=discount_id)
    
    if discount.company != company:
        raise Http404
    
    if not request.user.has_perm('pos.delete_discount'):
        return error(_("You have no permission to delete discounts."))
    
    discount.delete()
    
    return redirect('pos:list_discounts', company=company.url_name)
