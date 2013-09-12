# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: registration and company details
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from pos.models import Company, Category, Contact, Discount, Product, Price
from pos.views.util import error, JSON_response, JSON_parse, \
                           resize_image, validate_image, has_permission, \
                           no_permission_view
from common import globals as g
from common import unidecode
from common.functions import get_random_string

import re

###
### helper functions etc
###
def is_url_name_unique(url_name):
    try:
        Company.objects.get(url_name=url_name)
        # select succeeded, url_name exists
        return False
    except Company.DoesNotExist:
        # it does not exist.
        return True
    
    # ??? any other exceptions?
    return False

def check_url_name(url_name):
    # a valid url name:
    # 1. must not be equal to g.MISC['management_url']
    if url_name == g.MISC['management_url']:
        return False
    
    #  2. length between 1 and max_len
    #  3. allowed characters: alphanumeric and dash
    #  4. must not begin or end with dash
    rem = re.match('^\w\w*(?:-\w+)*$', url_name)
    try:
        if rem.group(0) == url_name:
            #  5. must be unique within the database
            if is_url_name_unique(url_name):
                return True
            else:
                return False
        else:
            return False
    except:
        return False
    
def unique_url_name(url_name):
    # check if url exists already and if it does, append a number
    # and return a unique url.
    
    max_len = g.MISC['company_url_length']
    # first, check for length
    if len(url_name) > max_len:
        url_name = url_name[0:max_len]
    
    # if there's already a url_name entry in database, return url_name-n, the first available name
    n = 1
    try_name = url_name
    while True:
        if is_url_name_unique(try_name):
            return try_name
        else:
            try_name = url_name[0:max_len - 1 - len(str(n))] + '-' + str(n)
            n += 1

def url_name_suggestions(request):
    # there's a 'name' in request:
    # take it and return a list of a few company url suggestions
    suggestions = []
    
    try: # get name from sent data
        name = JSON_parse(request.POST.get('data'))['name']
    except:
        return JSON_response({'suggestions':[]})
    
    # 0. "lowercaseize"
    name = name.lower()
    
    # 1. "asciify"
    s = unidecode.unidecode(name)
    
    # 2. remove forbidden characters (everything but alphanumeric and dash) ("alphanumerify")
    s = re.sub(r'[^\w-]', ' ', s).strip()
    
    # first suggestion: full name - also remove duplicate -'s
    suggestions.append(unique_url_name(re.sub(r' +', '-', s)))
    
    # 2. remove one-character words ("unonecharacterify")
    # regex: one character followed by a space at the beginning OR
    # space followed by a character followed by a space OR
    # space followed by a character at the end
    s = re.sub(r'(^. )|(( ).(?= ))|( .$)', ' ', s)
    
    # 3. suggestions:
    # first word, then first and second, then ..., up to g.MISC['company_url_length'] chars
    max_len = g.MISC['company_url_length']
    words = s.split()
    
    for w in range(1, len(words)+1):
        s = ''
        for i in range(w):
            s += '-' + words[i]
            
        s = s[1:] # cut off the first '-'
        if len(s) >= max_len:
            break
        
        suggestions.append(unique_url_name(s))
    
    # only first characters of every word (a.k.a. acronym)
    s = ''
    for w in words:
        s += w[0]
    suggestions.append(unique_url_name(s))

    # 4. remove possible inapropriate suggestions
    valid = []
    for s in suggestions:
        if check_url_name(s):
            valid.append(s)
    
    # 5. remove duplicates
    valid = list(set(valid))
    
    # 6. sort by length
    valid.sort(key=len)
    suggestions = valid
    del valid
    
    # 3a. add a random string to suggestions
    suggestions.append(unique_url_name(get_random_string(length=5).lower()))
    
    # pass on to the page
    return JSON_response({'suggestions':suggestions})

###############
### company ###
###############
class CompanyForm(forms.ModelForm):
    # take special case of urls
    def clean_url_name(self):
        url_name = self.cleaned_data['url_name']
        
        if 'url_name' in  self.initial:
            initial_url_name = self.initial['url_name']
        else:
            initial_url_name = ""
            
        if url_name == initial_url_name:
            return url_name
        
        if not check_url_name(url_name):
            raise forms.ValidationError(_("Url of the company is invalid or exists already."))
        else:
            return url_name

    def clean_image(self):
        return validate_image(self)

    class Meta:
        model = Company
        fields = ['name',
                  'url_name',
                  'email',
                  'image',
                  'street',
                  'postcode',
                  'city',
                  'country',
                  'phone',
                  'vat_no',
                  'notes']

# registration
@login_required
def register_company(request):
    # permissions: anybody can register a company
    
    # show CompanyForm, empty
    if request.method == 'POST':
        # submit data
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(False)
            company.created_by = request.user
            form.save()
            
            # continue with registration
            return redirect('pos:home', company=form.cleaned_data['url_name']) # home page
    else:
        # show an empty form
        form = CompanyForm()
    
    # some beautifixes:
    # future store url: same as this page's, excluding what's after the
    # g.MISC['management_url'] string
    # blocklogic.net/pos/app/register-company >> blocklogic.net/pos/company-name
    full_url = request.build_absolute_uri()
    pos_url = full_url[:full_url.rfind(g.MISC['management_url'] + '/')]   
    
    context = {
       'form':form,
       'pos_url':pos_url,
       'logo_dimensions':g.IMAGE_DIMENSIONS['logo'],
       'title':_("Registration"),
       'site_title':g.MISC['site_title'],
    }

    return render(request, 'pos/manage/register.html', context)

# edit after registration
@login_required
def edit_company(request, company):
    # get company, it must exist
    c = get_object_or_404(Company, url_name = company)
        
    # check if the user has permission to change it
    # only admins can change company details
    if not has_permission(request.user, c, 'company', 'edit'):
        return no_permission_view(request, c, _("edit company details"))
    
    context = {}
    
    if request.method == 'POST':
        # submit data
        form = CompanyForm(request.POST, request.FILES, instance=c)
        
        if form.is_valid():
            # save form and resize image to the maximum size that will ever be needed
            form.save()
            resize_image(c.image.path, g.IMAGE_DIMENSIONS['logo'])
            # for an eventual message for the user
            context['saved'] = True
            # if url_name was changed, redirect to new address
            return redirect('pos:edit_company', company=c.url_name)
    else:
        form = CompanyForm(instance=c)
        
    context['form'] = form
    context['company'] = c
    context['logo_dimensions'] = g.IMAGE_DIMENSIONS['logo']
    context['title'] = _("Company details")
    context['site_title'] = g.MISC['site_title']
    
    return render(request, 'pos/manage/company.html', context)