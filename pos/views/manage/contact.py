from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _, get_language
from django import forms
from django.http import Http404

from pos.models import Company, Contact, Country
from common import globals as g
from config.functions import get_date_format
from pos.views.util import JSON_response, JSON_error, has_permission, no_permission_view, format_date, \
    max_field_length, parse_date, manage_delete_object

import re


################
### contacts ###
################
class ContactForm(forms.Form):
    # do not use forms.ModelForm - we're formatting numbers and dates in our way

    # countries list for ChoiceField
    countries = [(c.two_letter_code, c.name) for c in Country.objects.all()]

    type = forms.ChoiceField(required=True, choices=g.CONTACT_TYPES)  # thid field will be hidden in the form
    # none of the fields are required (the form doesn't know for the company/individual whatchamacallit -
    # stuff will be checked in validate_contact)
    company_name = forms.CharField(required=False, max_length=max_field_length(Contact, 'company_name'))
    first_name = forms.CharField(required=False, max_length=max_field_length(Contact, 'first_name'))
    last_name = forms.CharField(required=False, max_length=max_field_length(Contact, 'last_name'))
    sex = forms.ChoiceField(choices=g.SEXES, required=False)
    street_address = forms.CharField(required=False, max_length=max_field_length(Contact, 'street_address'))
    postcode = forms.CharField(required=False, max_length=max_field_length(Contact, 'postcode'))
    city = forms.CharField(required=False, max_length=max_field_length(Contact, 'city'))
    state = forms.CharField(required=False, max_length=max_field_length(Contact, 'state'))
    country = forms.ChoiceField(required=False, choices=countries)
    # except that email is required in any case
    email = forms.EmailField(required=True, max_length=max_field_length(Contact, 'email'))
    phone = forms.CharField(required=False, max_length=max_field_length(Contact, 'phone'))
    vat = forms.CharField(required=False, max_length=max_field_length(Contact, 'vat'))
    date_of_birth = forms.CharField(required=False, max_length=g.DATE['max_date_length'])

    def clean(self):
        r = validate_contact(self.user, self.company, self.cleaned_data)
        if not r['status']:
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
    # state
    # email*
    # phone
    # vat

    def err(msg):  # the value that is returned if anything goes wrong
        return {'status': False, 'data': None, 'message': msg}

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
        
        # sex: must be in g.SEXES
        if 'sex' not in data and data['sex'] not in [x[0] for x in g.SEXES]:
            return err(_("Wrong sex"))
        
        # date of birth: parse date
        if 'date_if_birth' in data and len(data['date_of_birth']) > 0:
            r = parse_date(user, company, data['date_of_birth'])
            if not r['success']:
                return err(_("Wrong format of date of birth"))
            else:
                data['date_of_birth'] = r['date']
        else:
            data['date_of_birth'] = None
        
    # check credentials for company
    else:
        if not data.get('company_name'):
            return err(_("No company name"))
            
        if len(data['company_name']) > max_field_length(Contact, 'company_name'):
            return err(_("Company name too long"))
        
        # one shalt not save u'' into date field.
        data['date_of_birth'] = None
            
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
    m = re.search('([\w.-]+)@([\w.-]+)', data['email'])
    if data['email'] not in m.group(0):
        return err(_("Invalid email address"))

    # country: check for correct code
    if 'country' in data and data['country']:
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
    return {'status': True, 'data': data, 'message': None}


def get_all_contacts(user, company):
    contacts = Contact.objects.filter(company=company)

    r = []
    for c in contacts:
        r.append(contact_to_dict(user, company, c))

    return r


def contact_to_dict(user, company, c, send_to="python"):
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
    if c.sex:
        ret['sex'] = c.sex
    if c.date_of_birth:
        ret['date_of_birth'] = format_date(user, company, c.date_of_birth, send_to=send_to)
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
        ret['country_code'] = c.country.two_letter_code
    if c.email:
        ret['email'] = c.email
    if c.phone:
        ret['phone'] = c.phone
    if c.vat:
        ret['vat'] = c.vat

    return ret


@login_required
def list_contacts(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'contact', 'list'):
        return no_permission_view(request, c, _("view contacts"))

    l = request.GET.get('letter')
    results_display = False  # true if there was something in the search form

    # show the filter form
    if request.method == 'POST':
        contacts = Contact.objects.all()
        form = ContactFilterForm(request.POST)
        results_display = True

        if form.is_valid():
            # filter by whatever is in the form
            if form.cleaned_data['type'] == 'Individual':
                contacts = contacts.filter(type='Individual')
                if 'name' in form.cleaned_data:  # search by first and last name
                    first_names = contacts.filter(first_name__icontains=form.cleaned_data['name'])
                    last_names = contacts.filter(last_name__icontains=form.cleaned_data['name'])
                    contacts = (first_names | last_names).distinct()
            else:
                contacts = contacts.filter(type='Company')
                if 'name' in form.cleaned_data:  # search by company name
                    contacts = contacts.filter(company_name__icontains=form.cleaned_data['name'])
    else:
        form = ContactFilterForm()

        if l:
            if l == '*':
                # get all contacts that don't begin with any letter of the alphabet
                print r'^[^' + g.ALPHABETS[get_language()] + '].*'
                contacts = Contact.objects.filter(company=c,
                                                  company_name__iregex=r'^[^' + g.ALPHABETS[get_language()] + '].*') | \
                           Contact.objects.filter(company=c,
                                                  first_name__iregex=r'^[^' + g.ALPHABETS[get_language()] + '].*')
                print contacts
            else:
                # get contacts beginning with the selected letter
                contacts = Contact.objects.filter(company=c, company_name__istartswith=l) | \
                           Contact.objects.filter(company=c, first_name__istartswith=l)
        else:
            contacts = Contact.objects.none()
        
    context = {
        'company': c,
        'letter': l,
        'contacts': contacts,
        'filter_form': form,
        'results_display': results_display,
        'title': _("Contacts"),
        'site_title': g.MISC['site_title'],
        'date_format_django': get_date_format(request.user, c, 'django'),
        'alphabet': g.ALPHABETS[get_language()],
    }

    return render(request, 'pos/manage/contacts.html', context)


@login_required
def get_contact(request, company, contact_id):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company doest not exist"))
    
    # permissions: needs to be guest to view contacts
    if not has_permission(request.user, c, 'contact', 'list'):
        return JSON_error(_("You have no permission to view products"))
   
    contact = get_object_or_404(Contact, id=contact_id, company=c)
   
    return JSON_response(contact_to_dict(request.user, c, contact))
   

@login_required
def add_contact(request, company):
    # add a new contact
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'contact', 'edit'):
        return no_permission_view(request, c, _("add contacts"))

    t = request.GET.get('type')
    if not t:
        t = 'Individual'  # the default

    context = {
        'add': True,
        'type': t,
        'company': c,
        'title': _("Add contact"),
        'site_title': g.MISC['site_title'],
        'date_format_js': get_date_format(request.user, c, 'js')
    }

    if request.method == 'POST':
        # submit data
        form = ContactForm(request.POST)
        form.user = request.user
        form.company = c

        if form.is_valid():
            # create a new Contact
            contact = Contact(
                type=form.cleaned_data.get('type'),
                company_name=form.cleaned_data.get('company_name'),
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                sex=form.cleaned_data.get('sex'),
                street_address=form.cleaned_data.get('street_address'),
                postcode=form.cleaned_data.get('postcode'),
                city=form.cleaned_data.get('city'),
                state=form.cleaned_data.get('state'),
                country=form.cleaned_data.get('country'),
                email=form.cleaned_data.get('email'),
                phone=form.cleaned_data.get('phone'),
                vat=form.cleaned_data.get('vat'),
                date_of_birth=form.cleaned_data.get('date_of_birth'),
                
                created_by=request.user,
                company=c
            )
            contact.save()

            return redirect('pos:list_contacts', company=c.url_name)
    else:
        form = ContactForm(initial={'type': t})
        form.user = request.user
        form.company = c

    context['form'] = form
    
    return render(request, 'pos/manage/contact.html', context)


@login_required
def edit_contact(request, company, contact_id):
    # edit an existing contact
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'contact', 'edit'):
        return no_permission_view(request, c, _("edit contacts"))
    
    context = {
        'company': c,
        'contact_id': contact_id,
        'title': _("Edit contact"),
        'site_title': g.MISC['site_title'],
        'date_format_js': get_date_format(request.user, c, 'js'),
    }
    
    # get contact
    contact = get_object_or_404(Contact, id=contact_id)
        
    # check if contact actually belongs to the given company
    if contact.company != c:
        raise Http404
        
    if request.method == 'POST':
        # submit data
        form = ContactForm(request.POST)
        form.user = request.user
        form.company = c

        if form.is_valid():
            contact.type = form.cleaned_data.get('type')
            contact.company_name = form.cleaned_data.get('company_name')
            contact.first_name = form.cleaned_data.get('first_name')
            contact.last_name = form.cleaned_data.get('last_name')
            contact.sex = form.cleaned_data.get('sex')
            contact.date_of_birth = form.cleaned_data.get('date_of_birth')
            contact.street_address = form.cleaned_data.get('street_address')
            contact.postcode = form.cleaned_data.get('postcode')
            contact.city = form.cleaned_data.get('city')
            contact.state = form.cleaned_data.get('state')
            contact.country = form.cleaned_data.get('country')
            contact.email = form.cleaned_data.get('email')
            contact.phone = form.cleaned_data.get('phone')
            contact.vat = form.cleaned_data.get('vat')
            contact.save()
            
            return redirect('pos:list_contacts', company=c.url_name)
    else:
        initial = contact_to_dict(request.user, c, contact)
        form = ContactForm(initial=initial)
        form.user = request.user
        form.company = c

    context['form'] = form
    context['type'] = contact.type
    
    return render(request, 'pos/manage/contact.html', context)


def delete_contact(request, company):
    return manage_delete_object(request, company, Contact, (_("You have no permission to delete contacts"),
                                                            _("Could not delete contact")))