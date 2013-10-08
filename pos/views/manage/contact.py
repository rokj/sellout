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
from pos.views.util import JSON_response, JSON_parse, JSON_error, has_permission, no_permission_view, format_date

from rest_framework.decorators import api_view, permission_classes,\
    authentication_classes
from rest_framework.permissions import IsAuthenticated

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
    print cs
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
        form = ContactForm()
        
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
def delete_contact(request, company, contact_id):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'contact', 'edit'):
        return no_permission_view(request, c, _("delete contacts"))
    
    contact = get_object_or_404(Contact, id=contact_id)
    
    if contact.company != c:
        raise Http404

    contact.delete()
    
    return redirect('pos:list_contacts', company=c.url_name)
