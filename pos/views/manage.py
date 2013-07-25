from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db import transaction
from django.core.paginator import Paginator
from django.forms import ModelForm
import re

from pos.models import Company
from util import error, JSON_response, JSON_parse
from common import globals as g
from common import unidecode



from django.http import HttpResponse
from string import lower

### editing company details
class CompanyInfoForm(ModelForm):
    """def clean_url_name(self):
        data = self.cleaned_data['url_name']
        
        if data:
            # check if url_name contains anything else but characters, numbers and dashes
            match = re.match(r'^[\w-]{1,' + g.MISC['company_url_length'] + '}$', data)
            if not match:
                # there's something wrong with the name
                raise ValidationError()
            
            
import re

        if matchObj:
       print "matchObj.group() : ", matchObj.group()
       print "matchObj.group(1) : ", matchObj.group(1)
       print "matchObj.group(2) : ", matchObj.group(2)
    else:
       print "No match!!"
            pass"""
    
    class Meta:
        model = Company
        fields = ['name',
                  'image',
                  'street',
                  'postcode',
                  'city',
                  'country',
                  'email',
                  'phone',
                  'vat_no',
                  'notes',
                  'url_name']


# registration
def register_company(request):
    # show CompanyInfoForm, empty
    if request.method == 'POST':
        # submit data
        form = CompanyInfoForm(request.POST)
        if form.is_valid():
            # checking
            
            form.save()
    else:
        # show an empty form
        form = CompanyInfoForm()
    
    # some beautifixes:
    # future store location: same as this, except what's after the last slash, i.e.:
    # blocklogic.net/pos/register-company >> blocklogic.net/pos/company-name
    full_url = request.build_absolute_uri()
    pos_url = full_url[:full_url.rfind('/')+1]   
    
    context = {
       'form':form,
       'pos_url':pos_url,
    }

    return render(request, 'pos/register_company.html', context)

def check_url_name(url_name):
    # a valid url name:
    #  - length between 1 and max_len
    #  - allowed characters: alphanumeric and dash
    #  - must not begin or end with dash
    
    # regex should match, otherwise it's not
    rem = re.match('^\w\w*(?:-\w+)*$', url_name)
    try:
        if rem.group(0) == url_name:
            return True
        else:
            return False
    except:
        return False
    
def unique_url_name(url_name):
    max_len = g.MISC['company_url_length']
    # first, check for length
    if len(url_name) > max_len:
        url_name = url_name[0:max_len]
    
    # if there's already a url_name entry in database, return url_name-n, the first available name
    n = 1
    try_name = url_name
    while True:
        try:
            Company.objects.get(url_name=try_name)
            # succes, id exists, make a new name
            # shorten for length of '-n', if necessary
            try_name = url_name[0:max_len - 1 - len(str(n))] + '-' + str(n)
            n += 1
        except Company.DoesNotExist:
            # the name is available, return it 
            return try_name

def url_name_suggestions(request):
    # there's a 'name' in request:
    # take it and return a list of a few company url suggestions
    no_suggestions = {'suggestions':None}
    suggestions = []
    
    try: # get name from sent data
        name = JSON_parse(request.POST.get('data'))['name']
    except:
        return JSON_response(no_suggestions)
    
    # 0. lowercasize
    name = name.lower()
    
    # 1. ascii-fy string
    s = unidecode.unidecode(name)
    
    # 2. remove forbidden characters (everything but alphanumeric and dash
    s = re.sub(r'[^\w-]', ' ', s).strip()
    
    # first suggestion: full name - also remove duplicate -'s
    suggestions.append(unique_url_name(re.sub(r' +', '-', s)))
    
    # 2. remove one-character words
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
    
    # pass on to the page
    return JSON_response({'suggestions':suggestions})

def edit_company_details(request, company=None, company_id=None):
    # get company
    if company:
        c = get_object_or_404(Company, url_name = company)
    else:
        c = get_object_or_404(Company, id=company_id)
    
    # check if the user has permission to change it
    if not request.user.has_perm('pos.change_company'):
        return error(request, _("You have no permission to edit company details."))
    
    context = {}
    context['id'] = c.id
    
    if request.method == 'POST':
        # submit data
        form = CompanyInfoForm(request.POST, instance=c)
        if form.is_valid():
            # check a  
            
            # OK, save and show the form with the new data
            form.save()
            context['saved'] = True
    else:
        form = CompanyInfoForm(instance=c)
        
    context['form'] = form

    return render(request, 'pos/manage_company.html', context)