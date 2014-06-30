from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from pos.models import Company, Tax
from common import globals as g
from config.functions import get_company_value
from pos.views.util import JSON_response, JSON_parse, JSON_error, JSON_ok, \
                            has_permission, no_permission_view, \
                            format_number, \
                            max_field_length, \
                            parse_decimal


def tax_to_dict(user, company, tax):
    return {
        'id': tax.id,
        'name': tax.name,
        'amount': format_number(user, company, tax.amount),
        'default': tax.default,
    }


def get_default_tax(user, company):
    """ returns the default tax id and formatted value in dictionary: {id:<id>, amount:<amount>} 
        if there's no default tax, return the first one
        if there's no taxes at all, return zeros
        if there are many default taxes, return the one with the lowest id """
    try:
        # the 'normal' scenario: there's one default tax
        tax = Tax.objects.get(company=company, default=True)
    except Tax.MultipleObjectsReturned:  # more than one default tax, use the first by id
        tax = Tax.objects.filter(company=company, default=True).order_by('id')[0]
    except Tax.DoesNotExist:  # no default tax specified, use the first by id
        try:
            tax = Tax.objects.filter(company=company).order_by('id')[0]
        except: # even that doesn't work
            return {'id': 0,'amount': 0}

    return {'id': tax.id, 'amount': format_number(user, company, tax.amount)}


def validate_tax(user, company, tax):
    # validate_product, validate_discount, validate_contact for more info
    def err(msg):
        return {'success':False, 'data':None, 'message':msg}

    # name: check length
    if len(tax['name']) > 0:
        if len(tax['name']) > max_field_length(Tax, 'name'):
            return err(_("Name too long"))
    
    # amount: try to parse number
    if tax['amount']:
        r = parse_decimal(user, company, tax['amount'])
        if r['success']:
            tax['amount'] = r['number']  # this could
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
def list_taxes(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # permissions
    list_permission = has_permission(request.user, c, 'tax', 'list')
    edit_permission = has_permission(request.user, c, 'tax', 'edit')
    
    if not list_permission:
        return no_permission_view(request, c, _("You have no permission to view taxes"))
    
    context = {
        'company': c,
        'edit_permission': edit_permission,
        'title': _("Manage Tax Rates"),
        'site_title': g.MISC['site_title'],
        
        'separator': get_company_value(request.user, c, 'pos_decimal_separator'),
    }
    
    return render(request, 'pos/manage/tax.html', context)

@login_required
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
        r.append(tax_to_dict(request.user, c, t))
    
    return JSON_response(r)


@login_required
def add_tax(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))



    pass


@login_required
def edit_tax(request, company):
    # the company
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # the data
    data = JSON_parse(request.POST.get('data'))
    

    # get the tax
    tax = Tax.objects.get


@login_required
def delete_tax(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))


    pass