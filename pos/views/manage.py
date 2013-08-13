# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: company, categories, products,
# contacts, discounts.


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from pos.models import Company, Category, Contact, Discount, Product, Price
from util import error, JSON_response, JSON_parse, resize_image, validate_image
from common import globals as g
from common import unidecode
from common.functions import get_random_string

import re
from decimal import *

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

###################
### manage home ###
###################
def manage_home(request, company):
    company = get_object_or_404(Company, url_name=company)
    
    context = {
               'company':company,
               }
    
    return render(request, 'pos/manage/manage.html', context)

###############
### company ###
###############
class CompanyForm(forms.ModelForm):
    # take special case of urls
    def clean_url_name(self):
        url_name = self.cleaned_data['url_name']
        
        # if there was no change made, don't check
        initial_url_name = self.initial['url_name']
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
       'logo_dimensions':g.IMAGE_DIMENSIONS['logo'],
    }

    return render(request, 'pos/manage/register.html', context)

# edit after registration
def edit_company(request, company):
    import time
    tic = time.time()
    # get company, it must exist
    c = get_object_or_404(Company, url_name = company)
        
    # check if the user has permission to change it
    if not request.user.has_perm('pos.change_company'):
        return error(request, _("You have no permission to edit company details."))

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
               
    toc = time.time()
    print toc-tic
                    
    return render(request, 'pos/manage/company.html', context)

####################
###  categories  ###
####################
class CategoryForm(forms.ModelForm):
    # take special case of urls
    def clean_image(self):
        return validate_image(self)

    class Meta:
        model = Category
        fields = ['name',
                  'description',
                  'image']

def get_all_categories(company_id, category_id=None, sort='name', data=[], level=0, json=False):
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
        # if json == true, add to dictionary rather than queryset
        if json:
            entry = {'id':c.id,
                'name':c.name,
                'description':c.description,
                'level':c.level}
            if c.image:
                entry['image'] = c.image.url
            else:
                entry['image'] = None
                
            data.append(entry)
        else:
            data.append(c)
        
        # append all children
        children = Category.objects.filter(company__id=company_id, parent__id=category_id).order_by(sort)
        level += 1
        for c in children:
            get_all_categories(company_id, c.id, data=data, level=level, sort=sort, json=json)
    else:
        cs = Category.objects.filter(company__id=company_id, parent=None).order_by(sort)
        for c in cs:
            get_all_categories(c.company.id, c.id, data=data, level=level, sort=sort, json=json)

    return data
    
def list_categories(request, company):
    company = get_object_or_404(Company, url_name=company)
    context = {
               'company':company,
               'categories':get_all_categories(company.id, data=[]),
               }
    
    return render(request, 'pos/manage/categories.html', context)

def add_category(request, company, parent_id=-1):
    # get company
    company = get_object_or_404(Company, url_name=company)
     
    # if parent_id == -1, this is a top-level category
    parent_id = int(parent_id)
    if parent_id == -1:
        parent = None
    else:
        parent = get_object_or_404(Category, id=parent_id)
        if parent.company != company:
            raise Http404
    # check permissions
    if not request.user.has_perm('pos.add_category'):
        return error(request, _("You have no permission to add categories."))
    
    context = {'company':company,
               'parent_id':parent_id,
               'add':True,
               'image_dimensions':g.IMAGE_DIMENSIONS['category'],
               }
    
    if request.method == 'POST':
        # submit data
        form = CategoryForm(request.POST, request.FILES) # instance = None
        
        if form.is_valid():
            # created_by and company_id (only when creatine a new category)
            category = form.save(False)
            category.parent = parent
            if 'created_by' not in form.cleaned_data:
                category.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                category.company_id = company.id
        
            form.save()

            if category.image:
                resize_image(category.image.path, g.IMAGE_DIMENSIONS['category'])
            
            return redirect('pos:list_categories', company=company.url_name)
    else:
        form = CategoryForm() # create a new category
        
    context['form'] = form

    return render(request, 'pos/manage/category.html', context)

def edit_category(request, company, category_id):
    company = get_object_or_404(Company, url_name=company)
    
    # get category
    category = get_object_or_404(Category, id=category_id)
    # check if category actually belongs to the given company
    if category.company != company:
        raise Http404 # this category does not exist for the current user
    # check if the user has permission to change it
    if not request.user.has_perm('pos.change_category'):
        return error(request, _("You have no permission to edit categories."))

    context = {'company':company.url_name, 'category_id':category_id}
    
    if request.method == 'POST':
        # submit data
        form = CategoryForm(request.POST, request.FILES, instance=category)
        
        if form.is_valid():
            # created_by and company_id (only when creatine a new category)
            category = form.save(False)
            if 'created_by' not in form.cleaned_data:
                category.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                category.company_id = company.id
        
            form.save()
            if category.image:
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
    context['image_dimensions'] = g.IMAGE_DIMENSIONS['category']
    
    return render(request, 'pos/manage/category.html', context)

def delete_category(request, company, category_id):
    company = get_object_or_404(Company, url_name=company)
    
    # get category
    category = get_object_or_404(Category, id=category_id)
    # check if category actually belongs to the given company
    if category.company != company:
        raise Http404 # this category does not exist for the current user
    # check if the user has permission to change it
    if not request.user.has_perm('pos.change_category'):
        return error(request, _("You have no permission to edit categories."))
    
    # delete the category and return to management page
    try:
        category.delete()
    except:
        pass
    
    return redirect('pos:list_categories', company=company.url_name)

################
### contacts ###
################
class ContactForm(forms.ModelForm):
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

class ContactFilterForm(forms.Form):
    type = forms.ChoiceField(required=True,
                             choices=g.CONTACT_TYPES)
    name = forms.CharField(required=False)

def list_contacts(request, company):
    company = get_object_or_404(Company, url_name=company)
    
    contacts = Contact.objects.filter(company__id=company.id)
    
    # show the filter form
    if request.method == 'POST':
        form = ContactFilterForm(request.POST)
        
        if form.is_valid():
            # filter by whatever is in the form
            if form.cleaned_data['type'] == 'individual':
                contacts = contacts.filter(type='Individual')
                
                if 'name' in form.cleaned_data: # search by first and last name 
                    first_names = contacts.filter(first_name__icontains=form.cleaned_data['name'])
                    last_names = contacts.filter(last_name__icontains=form.cleaned_data['name'])
                    contacts = (first_names | last_names).distinct()
            else:
                contacts = contacts.filter(type='Company')
            
                if 'name' in form.cleaned_data: # search by company name
                    contacts = contacts.filter(company_name__icontains=form.cleaned_data['name'])
    else:
        form = ContactFilterForm()
        
    # show contacts
    paginator = Paginator(contacts, g.MISC['contacts_per_page'])

    page = request.GET.get('page')
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    context = {
        'company':company,
        'contacts':contacts,
        'paginator':paginator,
        'filter_form':form,
    }

    return render(request, 'pos/manage/contacts.html', context) 

def add_contact(request, company):
    # add a new contact
    company = get_object_or_404(Company, url_name=company)
    context = {}
    context['company'] = company.url_name
    
    # check for permission for adding contacts
    if not request.user.has_perm('pos.add_contact'):
        return error(request, _("You have no permission to add contacts."))

    if request.method == 'POST':
        # submit data
        form = ContactForm(request.POST)
        
        if form.is_valid():
            # created_by and company_id
            contact = form.save(False)
            if 'created_by' not in form.cleaned_data:
                contact.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                contact.company_id = company.id
        
            form.save()
            
            return redirect('pos:list_contacts', company=company.url_name)
    else:
        form = ContactForm()
        
    context['form'] = form
    context['company'] = company
    context['add'] = True
    
    return render(request, 'pos/manage/contact.html', context)


def edit_contact(request, company, contact_id):
    # edit an existing contact
    company = get_object_or_404(Company, url_name=company)
    context = {}
    context['company'] = company
    context['contact_id'] = contact_id
    
    # get contact id
    contact = get_object_or_404(Contact, id=contact_id)
        
    # check if contact actually belongs to the given company
    if contact.company != company:
        raise Http404
        
        # check if user has permissions to change contacts
        if not request.user.has_perm('pos.change_contact'):
            return error(request, _("You have no permission to edit contacts."))

    if request.method == 'POST':
        # submit data
        form = ContactForm(request.POST, instance=contact)
        
        if form.is_valid():
            # created_by and company_id
            contact = form.save(False)
            if 'created_by' not in form.cleaned_data:
                contact.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                contact.company_id = company.id
        
            form.save()
            
            return redirect('pos:list_contacts', company=company.url_name)
    else:
        form = ContactForm(instance=contact)
        
    context['form'] = form
    
    return render(request, 'pos/manage/contact.html', context)

def delete_contact(request, company, contact_id):
    company = get_object_or_404(Company, url_name=company)
    contact = get_object_or_404(Contact, id=contact_id)
    
    if contact.company != company:
        raise Http404
    
    if not request.user.has_perm('pos.delete_contact'):
        return error(_("You have no permission to delete contacts."))
    
    contact.delete()
    
    return redirect('pos:list_contacts', company=company.url_name)

#################
### discounts ###
#################
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

###############
## products ###
###############
def JSON_categories(request, company):
    company = get_object_or_404(Company, url_name=company)
    
    # return all categories' data in JSON format
    return JSON_response(get_all_categories(company.id, sort='name', data=[], json=True))


def products(request, company):
    company = get_object_or_404(Company, url_name = company)
    
    context = {
               'company':company, 
               # TODO add title & site title
               }
    return render(request, 'pos/manage/products.html', context)

def search_products(request, company):
    
    import time
    
    tic = time.time()
    
    company = get_object_or_404(Company, url_name = company)
    
    # get all products from this company and filter them by entered criteria
    products = Product.objects.filter(company=company)
    
    criteria = JSON_parse(request.POST['data'])
    
    # general filter: search 
    general_filter = criteria['general_filter'].split(' ')
    print general_filter
    
    for w in general_filter:
        if w == '':
            continue
        # search categories, product_code, shop_code, name, description, notes, price
        products = (products.filter(category__name__icontains=w) | 
            products.filter(code__icontains=w) | 
            products.filter(shop_code__icontains=w) |
            products.filter(name__icontains=w) | 
            products.filter(description__icontains=w) | 
            products.filter(private_notes__icontains=w)) 
            # price is in 
        try:
            products = products | Product.objects.filter(pk__in=Price.objects.filter(unit_price=Decimal(w))) 
        except:
            pass
        
        products = products.distinct()
    
    # advanced filter: search by field
    
    
    
    toc = time.time()
    
    print toc - tic
    
    print products

    return JSON_response({'test':'tralala'});
