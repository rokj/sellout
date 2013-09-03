# author: nejc jurkovic
# date: 3. 9. 2013
#
# Views for managing POS data: home

from django.core.urlresolvers import reverse

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from pos.models import Company

###################
### manage home ###
###################
def manage_home(request, company):
    company = get_object_or_404(Company, url_name=company)
    
    context = {
               'company':company,
               }
    
    return render(request, 'pos/manage/manage.html', context)