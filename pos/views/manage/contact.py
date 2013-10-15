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

from pos.models import Company, Contact
from common import globals as g
from config.functions import get_date_format, get_value
from pos.views.util import JSON_response, JSON_ok, JSON_parse, JSON_error, has_permission, no_permission_view, format_date,\
    max_field_length, parse_date

from rest_framework.decorators import api_view, permission_classes,\
    authentication_classes
from rest_framework.permissions import IsAuthenticated
from config.models import Country

import re

################
### contacts ###
################
class ContactForm(forms.Form):
    # do not use forms.ModelForm - we're formatting numbers and dates in our way

    # countries list for ChoiceField
    countries = [(c.two_letter_code, c.name) for c in Country.objects.all()]

    type = forms.ChoiceField(choices=g.CONTACT_TYPES)
    # none of the fields are required (the form doesn't know for the company/individual whatchamacallit -
    # stuff will be checked in validate_contact)
    company_name = forms.CharField(required=False, max_length=max_field_length(Contact, 'company_name'))
    first_name = forms.CharField(required=False, max_length=max_field_length(Contact, 'first_name'))
    last_name = forms.CharField(required=False, max_length=max_field_length(Contact, 'last_name'))
    street_address = forms.CharField(required=False, max_length=max_field_length(Contact, 'street_address'))
    postcode = forms.CharField(required=False, max_length=max_field_length(Contact, 'postcode'))
    city = forms.CharField(required=False, max_length=max_field_length(Contact, 'city'))
    state = forms.CharField(required=False, max_length=max_field_length(Contact, 'state'))
    country = forms.ChoiceField(required=False, choices=countries)
    # except that email is required in any case
    email = forms.EmailField(required=True, max_length=max_field_length(Contact, 'email'))
    phone = forms.CharField(required=False, max_length=max_field_length(Contact, 'phone'))
    vat = forms.CharField(required=False, max_length=max_field_length(Contact, 'vat'))
    date_of_birth = forms.CharField(required=False, max_length=g.DATE_FORMATS['max_date_length'])
    
    def clean(self):
        r = validate_contact(self.user, self.company, self.cleaned_data)
        if not r['success']:
            raise forms.ValidationError(r['message'])
        else:
            return r['data']

class ContactFilterForm(forms.Form):
    type = forms.ChoiceField(required=True,
                             choices=g.CONTACT_TYPES)
    name = forms.CharField(required=False)

def validate_contact(user, company, data):
    # data format (*-required data):
    # type*
    # company_name* (only if Company)
    # first_name* (only if Individual)
    # last_name* (only if Individual)
    # date_of_birth - list of discount ids (checked in create/edit_product)
    # street_address
    # postcode
    # city
    # country
    # email*
    # phone
    # vat

    def err(msg): # the value that is returned if anything goes wrong
        return {'success':False, 'data':None, 'message':msg}

    # return:
    # status: True if validation passed, else False
    #  data: 'cleaned' data if validation succeeded, else False
    #  message: error message or empty if validation succeeded

    if 'type' not in data:
        return err(_("No type specified"))
    if data['type'] not in [x[0] for x in g.CONTACT_TYPES]:
        return err(_("Wrong contact type"))

    # check credentials for Individual
    if data['type'] == 'Individual':
        # first name: check length (mandatory)
        if not data.get('first_name'):
            return err(_("No first name"))
        elif len(data['first_name']) > max_field_length(Contact, 'first_name'):
            return err(_("First name too long"))
        
        # last name: check length (mandatory)
        if not data.get('last_name'):
            return err(_("No last name"))
        elif len(data['last_name']) > max_field_length(Contact, 'last_name'):
            return err(_("Last name too long"))
            
        # date of birth: parse date
        if len(data['date_of_birth']) > 0:
            r = parse_date(user, data['date_of_birth'])
            if not r['success']:
                return err(_("Wrong format of date of birth"))
            else:
                data['date_of_birth'] = r['date']
        else:
            del data['date_of_birth']
        
    # check credentials for company
    else:
        print data
        if not data.get('company_name'):
            return err(_("No company name"))
            
        if len(data['company_name']) > max_field_length(Contact, 'company_name'):
            return err(_("Company name too long"))
        
        # one shalt not save u'' into date field.
        del data['date_of_birth']
            
    # common fields:
    # email*
    if 'email' not in data:
        return err(_("Email is required"))
    if len(data['email']) > max_field_length(Contact, 'email'):
        return err(_("Email address too long"))
    # validate email with regex:
    # ^[\w\d._+%]+  a string with any number of characters, numbers, and ._+% signs
    # @[\w\d.-]{2,} an @ sign followed by domain name of at least 2 characters long (can contain . and -)
    # \.\w{2,4}$'   domain (2-4 alphabetic characters)
    m = re.search('^[\w\d._+%]+@[\w\d.-]{2,}\.\w{2,4}$', data['email'])
    if data['email'] not in m.group(0):
        return err(_("Invalid email address"))

    # country: check for correct code
    if data['country']:
        try:
            data['country'] = Country.objects.get(two_letter_code=data['country'])
        except Country.DoesNotExist:
            return err(_("Country does not exist"))
    
    # other, non-mandatory fields: check length only
    def check_length(d, l):
        if d:
            if len(d) > l:
                return False
            else:
                return True
        else:
            return True
        
    # street_address
    if not check_length(data.get('street_address'), max_field_length(Contact, 'street_address')):
        return err(_("Street address too long"))
        
    # postcode
    if not check_length(data.get('postcode'), max_field_length(Contact, 'postcode')):
        return err(_("Post code too long"))
        
    # city
    if not check_length(data.get('city'), max_field_length(Contact, 'city')):
        return err(_("City name too long"))
    
    # state 
    if not check_length(data.get('state'), max_field_length(Contact, 'state')):
        return err(_("State name too long"))
    
    # phone
    if not check_length(data.get('phone'), max_field_length(Contact, 'phone')):
        return err(_("Phone number too long"))

    # vat
    if not check_length(data.get('vat'), max_field_length(Contact, 'vat')):
        return err(_("VAT number too long"))

    # everything OK
    return {'success':True, 'data':data, 'message':None}

def contact_to_dict(user, c):
    # returns all relevant contact's data
    # id
    # type
    # company_name
    # first_name
    # last_name
    # date_of_birth
    # street_address
    # postcode
    # city
    # country
    # email
    # phone
    # vat
    ret = {}

    ret['id'] = c.id
    ret['type'] = c.type
    
    if c.company_name:
        ret['company_name'] = c.company_name
    if c.first_name:
        ret['first_name'] = c.first_name
    if c.last_name:
        ret['last_name'] = c.last_name
    if c.date_of_birth:
        ret['date_of_birth'] = format_date(user, c.date_of_birth)
    if c.street_address:
        ret['street_address'] = c.street_address
    if c.postcode:
        ret['postcode'] = c.postcode
    if c.city:
        ret['city'] = c.city
    if c.state:
        ret['state'] = c.state
    if c.country:
        ret['country'] = c.country.name
    if c.email:
        ret['email'] = c.email
    if c.phone:
        ret['phone'] = c.phone
    if c.vat:
        ret['vat'] = c.vat

    return ret


@login_required
def web_list_contacts(request, company):
    return list_contacts(request, company)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_list_contacts(request, company):
    return m_list_contacts(request, company)

def m_list_contacts(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
     
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'contact', 'list'):
        return JSON_error(_("You have no permission to view products"))
    
    contacts = Contact.objects.filter(company__id=c.id)
    
    criteria = JSON_parse(request.POST['data'])
    
    if criteria.get('type') == 'Individual':
        contacts = contacts.filter(type='Individual')
        if 'name' in criteria:
            first_names = contacts.filter(first_name__icontains=criteria.get('name'))
            last_names = contacts.filter(last_name__icontains=criteria.get('name'))
            contacts = (first_names | last_names).distinct()
    elif criteria.get('type') == 'Company':
      contacts = contacts.filter(type='Company')
      if 'name' in criteria:
          contacts = contacts.filter(company_name__icontains=criteria.get('name'))

    cs = []
    for c in contacts:
        cs.append(contact_to_dict(request.user, c))
    return JSON_response(cs)

def list_contacts(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'contact', 'list'):
        return no_permission_view(request, c, _("view contacts"))
    
    contacts = Contact.objects.filter(company__id=c.id)
    
    # show the filter form
    if request.method == 'POST':
        form = ContactFilterForm(request.POST)
        if form.is_valid():
            # filter by whatever is in the form
            if form.cleaned_data['type'] == 'Individual':
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
    paginator = Paginator(contacts, get_value(request.user, 'pos_contacts_per_page'))

    page = request.GET.get('page')
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    context = {
        'company':c,
        'contacts':contacts,
        'paginator':paginator,
        'filter_form':form,
        'title':_("Contacts"),
        'site_title':g.MISC['site_title'],
        'date_format_django':get_date_format(request.user, 'django'),
    }

    return render(request, 'pos/manage/contacts.html', context)

@login_required
def web_get_contact(request, company, contact_id):
    return get_contact(request, company, contact_id)

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_get_contact(request, company, contact_id):
    return get_contact(request, company, contact_id)

def get_contact(request, company, contact_id):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company doest not exist"))
    
    # permissions: needs to be guest to view contacts
    if not has_permission(request.user, c, 'contact', 'list'):
        return JSON_error(_("You have no permission to view products"))
   
    contact = get_object_or_404(Contact, id = contact_id, company = c)
   
    return JSON_response(contact_to_dict(request.user, contact))
   
   
@login_required
def web_add_contact(request, company):
    return add_contact(request, company)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_add_contact(request, company):
    return m_add_contact(request, company)

def m_add_contact(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # sellers can add product
    if not has_permission(request.user, c, 'product', 'edit'):
        return JSON_error(_("You have no permission to add products"))

    data = JSON_parse(request.POST['data'])
    
    # validate data
    valid = validate_contact(request.user, c, data)
    if not valid['status']:
        return JSON_error(valid['message'])
    data = valid['data']
    
    print ("bla")
    
    try:
        country = Country.objects.get(two_letter_code=data['country'])
    except Country.DoesNotExist:
        return JSON_error(_("Country does not exist"))
        
    contact = Contact(
        company = c,
        created_by = request.user,
        type = data['type'],
        first_name = data['first_name'],
        last_name = data['last_name'],
        #date_of_birth = data['date_of_birth'],
        street_address = data['street_address'],
        postcode = data['postcode'],
        city = data['city'],
        state = data['state'],
        country = country,
        email = data['email'],
        phone = data['phone'],
        #vat = data['vat']
    )
    contact.save()
    return JSON_ok()


def add_contact(request, company):
    # add a new contact
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'contact', 'edit'):
        return no_permission_view(request, c, _("add contacts"))
    
    context = {
        'add':True,
        'company':c,
        'title':_("Add contact"),
        'site_title':g.MISC['site_title'],
        'date_format_jquery':get_date_format(request.user, 'jquery')
    }

    if request.method == 'POST':
        # submit data
        form = ContactForm(request.POST)
        form.user = request.user
        form.company = c

        if form.is_valid():
            # create a new Contact
            contact = Contact(
                type = form.cleaned_data.get('type'),
                company_name = form.cleaned_data.get('company_name'),
                first_name = form.cleaned_data.get('first_name'),
                last_name = form.cleaned_data.get('last_name'), 
                street_address = form.cleaned_data.get('street_address'),
                postcode = form.cleaned_data.get('postcode'),
                city = form.cleaned_data.get('city'),
                state = form.cleaned_data.get('state'),
                country = form.cleaned_data.get('country'),
                email = form.cleaned_data.get('email'),
                phone = form.cleaned_data.get('phone'),
                vat = form.cleaned_data.get('vat'),
                date_of_birth = form.cleaned_data.get('date_of_birth'),
                
                created_by = request.user,
                company = c

            )
            contact.save()

            return redirect('pos:list_contacts', company=c.url_name)
    else:
        form = ContactForm()
        form.user = request.user
        form.company = c

    context['form'] = form
    
    return render(request, 'pos/manage/contact.html', context)

@login_required
def web_edit_contact(request, company, contact_id):
    return edit_contact(request, company, contact_id)

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_contact(request, company, contact_id):
    return m_edit_contact(request, company, contact_id)

def m_edit_contact(request, company, contact_id):
    # update existing contact
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))
    
    # sellers can edit product
    if not has_permission(request.user, c, 'product', 'edit'):
        return JSON_error(_("You have no permission to edit products"))

    data = JSON_parse(request.POST['data'])
    
    try:
        contact = Contact.objects.get(id=contact_id)
    except:
        return JSON_error(_("Contact doest not exist"))
    
    valid = validate_contact(request.user, c, data)
    if not valid['status']:
        return JSON_error(valid['messege'])
    data = valid[data]

    contact.company = data['company_name']
    contact.type = data['type']
    contact.company_name = data['company_name']
    contact.first_name = data['first_name']
    contact.last_name = data['last_name']
    contact.date_of_birth = data['date_of_birth']
    contact.street_address = data['street_address']
    contact.postcode = data['postcode']
    contact.city = data['city']
    contact.state = data['state']
    contact.country = data['country']
    contact.email = data['email']
    contact.phone = data['phone']
    contact.vat = data['vat']
    
    contact.save()
    
    return JSON_ok()
    
    

def edit_contact(request, company, contact_id):
    # edit an existing contact
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'contact', 'edit'):
        return no_permission_view(request, c, _("edit contacts"))
    
    context = {
        'company':c,
        'contact_id':contact_id,
        'title':_("Edit contact"),
        'site_title':g.MISC['site_title'],
        'date_format_jquery':get_date_format(request.user, 'jquery'),
    }
    
    # get contact
    contact = get_object_or_404(Contact, id=contact_id)
        
    # check if contact actually belongs to the given company
    if contact.company != c:
        raise Http404
        
    if request.method == 'POST':
        # submit data
        form = ContactForm(request.POST, instance=contact)

        if form.is_valid():
            # created_by and company_id
            contact = form.save(False)
            if 'created_by' not in form.cleaned_data:
                contact.created_by = request.user
            if 'company_id' not in form.cleaned_data:
                contact.company_id = c.id
        
            form.save()
            
            return redirect('pos:list_contacts', company=c.url_name)
    else:
        form = ContactForm(instance=contact)

    context['form'] = form
    
    return render(request, 'pos/manage/contact.html', context)

@login_required
def web_delete_contact(request, company, contact_id):
    return delete_contact(request, company, contact_id)

def mobile_delete_contact(request, company, contact_id):
    return

def delete_contact(request, company, contact_id):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'contact', 'edit'):
        return no_permission_view(request, c, _("delete contacts"))
    
    contact = get_object_or_404(Contact, id=contact_id)
    
    if contact.company != c:
        raise Http404

    contact.delete()


