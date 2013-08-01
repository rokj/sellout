from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.db import transaction
from django.core.paginator import Paginator
from django.forms import ModelForm, ValidationError
from django.http import HttpResponse, Http404

from pos.models import Company, Category, Contact
from util import error, JSON_response, JSON_parse, resize_image, validate_image
from common import globals as g
from common import unidecode
from common.functions import get_random_string

import re
import os

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

### 
### manage home
### 
def manage_home(request, company):
    company = get_object_or_404(Company, url_name=company)
    
    context = {
               'company':company,
               }
    
    return render(request, 'pos/manage/manage.html', context)

###
### editing company details
###
class CompanyForm(ModelForm):
    # take special case of urls
    def clean_url_name(self):
        url_name = self.cleaned_data['url_name']
        
        # if there was no change made, don't check
        initial_url_name = self.initial['url_name']
        if url_name == initial_url_name:
            return url_name
        
        if not check_url_name(url_name):
            raise ValidationError(_("Url of the company is invalid or exists already."))
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
def register_company(request):
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
    }

    return render(request, 'pos/manage/register.html', context)

# edit after registration
def edit_company(request, company):
    # get company, it must exist
    c = get_object_or_404(Company, url_name = company)
        
    # check if the user has permission to change it
    if not request.user.has_perm('pos.change_company'):
        return error(request, _("You have no permission to edit company details."))

    if c.image:
        old_image = c.image.name      # c gets overwritten
        old_image_path = c.image.path # on form submit
    else:
        old_image = None
        old_image_path = None
    
    context = {}
    
    if request.method == 'POST':
        # submit data
        form = CompanyForm(request.POST, request.FILES, instance=c)
        
        if form.is_valid():
            new_image = form.cleaned_data['image']
            
            # possible cases:
            # 1. new image upload: new_image and not old_image; RESIZE
            # 2. rewrite image: new_image != old_image; DELETE, RESIZE
            # 3. delete image: new_image = False; DELETE
            if new_image and not old_image: # 1.
                delete = False
                resize = True
            elif not new_image: # 3.
                delete = True
                resize = False
            elif new_image != old_image: # 2.
                resize = True
                delete = True
            
            if delete:
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            form.save()
            
            # resize logo to the desired dimensions (if needed)
            if resize:
                resize_image(c.image.path, g.IMAGE_DIMENSIONS['logo'])
            
            context['saved'] = True
            # if url_name was changed, redirect to new address
            return redirect('pos:edit_company', company=c.url_name)
    else:
        form = CompanyForm(instance=c)
        
    context['form'] = form
    context['company'] = c
    context['logo_dimensions'] = g.IMAGE_DIMENSIONS['logo']
                    
    return render(request, 'pos/manage/company.html', context)

###
### adding/editing categories
###
class CategoryForm(ModelForm):
    # take special case of urls
    def clean_image(self):
        return validate_image(self)

    class Meta:
        model = Category
        fields = ['name',
                  'description',
                  'image']

def get_all_categories(company_id, category_id=None, sort='name', data=[], level=0):
    # return a structured list of all categories (converted to dictionaries)
    
    #def category_to_dict(c, level): # c = Category object # currently not needed
    #    return {'id':c.id,
    #            'name':c.name,
    #            'description':c.description,
    #            'image':c.image,
    #            'level':level
    #    }
    
    if category_id:
        c = Category.objects.get(company__id=company_id, id=category_id)
        # add current category to list
        c.level = level
        #data.append(category_to_dict(c, level))
        data.append(c)
        
        # append all children
        children = Category.objects.filter(company__id=company_id, parent__id=category_id).order_by(sort)
        level += 1
        for c in children:
            get_all_categories(company_id, c.id, data=data, level=level, sort=sort)
    else:
        cs = Category.objects.filter(company__id=company_id, parent=None).order_by(sort)
        print cs
        for c in cs:
            get_all_categories(c.company.id, c.id, data=data, level=level, sort=sort)

    return data
    
def list_categories(request, company):
    company = get_object_or_404(Company, url_name=company)
    context = {
               'company':company,
               'categories':get_all_categories(company.id, data=[]),
               }
    
    return render(request, 'pos/manage/categories.html', context)

def add_category(request, company, parent_id):
    pass

def edit_category(request, company, category_id):
    # get company
    company = get_object_or_404(Company, url_name=company)
        
    # get category
    category = get_object_or_404(Category, id=category_id)
    # check if category actually belongs to the given company
    if category.company != company:
        raise Http404 # this category does not exist for the current user
    # check if the user has permission to change it
    if not request.user.has_perm('pos.change_category'):
        return error(request, _("You have no permission to edit categories."))

    # image handling
    try:
        old_image = category.image.name
        old_image_path = category.image.path
    except:
        old_image = None
        old_image_path = None
    
    context = {'company':company.url_name, 'category_id':category_id}
    
    if request.method == 'POST':
        # submit data
        form = CategoryForm(request.POST, request.FILES, instance=category)
        
        if form.is_valid():
            # image
            new_image = form.cleaned_data['image'] # see company form for comments
            
            print new_image
            print old_image
            if not old_image and new_image: # currently no image exists
                delete = False
                resize = True
            elif old_image and not new_image : # clear checkbox was checked 
                delete = True
                resize = False
            elif new_image != old_image: # image replacement
                resize = True
                delete = True
            else: # whatever
                delete = False
                resize = False
            
            #if delete:
                # delete all files on old_image_path* (that includes all generated thumbnails)
                #import glob
                #for f in glob.glob(old_image_path + '*'):
                #    print 'removing ' + f
                #    #Do what you want with the file
                #    os.remove(f)
            
            # created_by and company_id (only when creatine a new category)
            category = form.save(False)
            if 'created_by' not in form.cleaned_data:
                category.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                category.company_id = company.id
        
            form.save()
            
            if resize:
                resize_image(category.image.path, g.IMAGE_DIMENSIONS['category'])
            
            return redirect('pos:list_categories', company=company.url_name)
    else:
        if category:
            form = CategoryForm(instance=category) # update existing category
        else:
            form = CategoryForm() # create a new category
        
    context['form'] = form
    context['company'] = company
    context['category'] = category
    
    return render(request, 'pos/manage/category.html', context)

def delete_category(request, company, category_id):
    pass

### 
### contacts
### 
class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = ['type',
                  'company_name',
                  'first_name',
                  'last_name',
                  'date_of_birth',
                  'street_address',
                  'postcode',
                  'city',
                  'country', 
                  'email',
                  'phone',
                  'vat']

def edit_contact(request, company, contact_id):
    pass
"""
    # get company
    company = get_object_or_404(Company, url_name=company)
    
    # get category
    contact = get_object_or_404(Category, id=contact_id)
    
    # check if contact actually belongs to the given company
    if contact.company != company:
        raise Http404 # this category does not exist for the current user

    # check if the user has permission to change it
    if not request.user.has_perm('pos.change_category'):
        return error(request, _("You have no permission to edit company details."))

    context = {'company':company.url_name, 'contact_id':contact_id}
    
    if request.method == 'POST':
        # submit data
        form = CategoryForm(request.POST, request.FILES, instance=category)
        
        if form.is_valid():
            new_image = form.cleaned_data['image'] # see company form for comments
            print new_image
            print old_image
            if new_image and not old_image:
                delete = False
                resize = True
            elif not new_image:
                delete = True
                resize = False
            elif new_image != old_image:
                resize = True
                delete = True
            else:
                delete = False
                resize = False
            
            if delete:
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            form.save()
            
            if resize:
                resize_image(category.image.path, g.IMAGE_DIMENSIONS['category'])
            
            context['saved'] = True
            return redirect('pos:edit_category', company=company.url_name, category_id=category.id)
    else:
        form = CategoryForm(instance=category)
        
    context['form'] = form
    context['image'] = category.image
    
    return render(request, 'pos/manage/category.html', context)
"""