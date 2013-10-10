from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from pos.models import Company, Tax
from common import globals as g
from config.functions import get_date_format, get_value
from pos.views.util import JSON_response, JSON_parse, JSON_error, has_permission, no_permission_view, format_date

from rest_framework.decorators import api_view, permission_classes,\
    authentication_classes
from rest_framework.permissions import IsAuthenticated

#################
### tax rates ###
#################
def list_taxes(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # permissions
    list_permission = has_permission(request.user, c, 'tax', 'list')
    edit_permission = has_permission(request.user, c, 'tax', 'edit')
    
    if not list_permission:
        return no_permission_view(_("You have no permission to view taxes"))
    
    if request.method == 'POST':
        # save all tax rates from request.POST
        # do saving as long as the request.POST.get('tax_name_<number>') returns anything
        Tax.objects.filter(company=c).delete()
        
        i = 0
        while True:
            name = 'tax_name_' + str(i)
            amount = 'tax_amount_' + str(i)
            
            if request.POST.get(name):
                # verify the data and add a new entry
                print request.POST.get(name)
            else:
                break
            
            i += 1
        
        # the 'new entry' (drop errors silently, checking and alerts will make jquery)
        """if request.POST.get('tax_name_new') and request.POST.get('tax_amount_new'):
            new_tax = Tax(
                created_by = request.user,
                amount = 
            
            )
            new_tax.save()
        """

    
    # show a simple list of tax rates
    taxes = Tax.objects.filter(company=c)
    
    context = {
        'company':c,
        'taxes':taxes,
        'edit_permission':edit_permission,
        'title':_("Manage Tax Rates"),
        'site_title':g.MISC['site_title'],
    }
    
    return render(request, 'pos/manage/tax.html', context)
    
