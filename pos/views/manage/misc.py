# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: contacts

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
    if not has_permission(request.user, c, 'tax', 'list'):
        return no_permission_view(_("You have no permission to view taxes"))
    
    # show a simple list of tax rates
    taxes = Tax.objects.filter(company=c)
    
    context = {
        'company':c,
        'taxes':taxes
    }
    
    return render(request, 'pos/manage/tax.html', context)
    
