from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from pos.models import Company, Tax
from common import globals as g
from config.functions import get_date_format, get_value
from pos.views.util import JSON_response, JSON_parse, JSON_error, JSON_ok, \
                            has_permission, no_permission_view, \
                            format_date, format_number, \
                            max_field_length, \
                            parse_decimal
from rest_framework.decorators import api_view, permission_classes,\
    authentication_classes
from rest_framework.permissions import IsAuthenticated

def tax_to_dict(user, tax):
    return {
        'id':tax.id,
        'name':tax.name,
        'amount':format_number(user, tax.amount),
        'default':tax.default,
    }

def get_default_tax(user, company):
    """ returns the default tax id and formatted value in dictionary: {id:<id>, amount:<amount>} 
        if there's no default tax, return the first one
        if there's no taxes at all, return zeros
        if there are many default taxes, return the one with the lowest id """
    try:
        # the 'normal' scenario: there's one default tax
        tax = Tax.objects.get(company=company, default=True)
    except Tax.MultipleObjectsReturned: # more than one default tax, use the first by id
        tax = Tax.objects.filter(company=company, default=True).order_by('id')[0]
    except Tax.DoesNotExist: # no default tax specified, use the first by id
        try:
            tax = Tax.objects.filter(company=company).order_by('id')[0]
        except: # even that doesn't work
            return {'id':0,'amount':0}

    return {'id':tax.id, 'amount':format_number(user, tax.amount)}

def validate_tax(user, tax):
    # validate_product, validate_discount, validate_contact for more info
    def err(msg):
        return {'success':False, 'data':None, 'message':msg}

    # name: check length
    if len(tax['name']) > 0:
        if len(tax['name']) > max_field_length(Tax, 'name'):
            return err(_("Name too long"))
    
    # amount: try to parse number
    if tax['amount']:
        r = parse_decimal(user, tax['amount'])
        if r['success']:
            tax['amount'] = r['number'] # this could 
        else:
            return err(_("Wrong number format for amount"))
    else:
        # amount is mandatory
        return err(_("No amount entered"))

    # default: does not matter
        
    return {'success':True, 'data':tax, 'message':None}


#################
### tax rates ###
#################

@login_required
def web_list_taxes(request, company):
    return list_taxes(request, company)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_list_taxes(request, company):
    return list_taxes(request, company)

def list_taxes(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # permissions
    list_permission = has_permission(request.user, c, 'tax', 'list')
    edit_permission = has_permission(request.user, c, 'tax', 'edit')
    
    if not list_permission:
        return no_permission_view(_("You have no permission to view taxes"))
    
    context = {
        'company':c,
        'edit_permission':edit_permission,
        'title':_("Manage Tax Rates"),
        'site_title':g.MISC['site_title'],
        
        'separator':get_value(request.user, 'pos_decimal_separator'),
    }
    
    return render(request, 'pos/manage/tax.html', context)

@login_required
def web_get_taxes(request, company):
    return get_taxes(request, company)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_taxes(request, company):
    return get_taxes(request, company)
    
def get_taxes(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    if not has_permission(request.user, c, 'tax', 'list'):
        return JSON_error(_("You have no permission to view taxes"))
        
    taxes = Tax.objects.filter(company=c)
    
    r = []
    for t in taxes:
        r.append(tax_to_dict(request.user, t))
    
    return JSON_response(r)
    
@login_required
def web_save_taxes(request, company):
    return save_taxes(request, company)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_save_taxes(request, company):
    return save_taxes(request, company)

def save_taxes(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    if not has_permission(request.user, c, 'tax', 'edit'):
        return JSON_error(_("You have no permission to edit taxes"))
    
    new_taxes = JSON_parse(request.POST['data'])
    old_tax_ids = [x.id for x in Tax.objects.filter(company=c).all()] # save ids of old taxes for later deletion
    
    default = None
    
    # validate first
    for t in new_taxes:
        r = validate_tax(request.user, t)
        if not r['success']:
            return JSON_error(t['name'] + ": " + r['message'])
        else:
            t = r['data']

    # enter new taxes
    for t in new_taxes:
        tax = Tax(
            created_by = request.user,
            company = c,
            amount = t['amount'],
            name = t['name'],
            default = False
        )
        if t['default'] and not default: # onlt the first 'default' can be the 'default'
                                         # (there should not be more than 1 marked as that anyway)
            tax.default = True
            default = True
            
        tax.save()
            
    # everything is ok, delete all old taxes from the database
    for i in old_tax_ids:
        Tax.objects.get(id=i).delete()
        
    return JSON_ok()
