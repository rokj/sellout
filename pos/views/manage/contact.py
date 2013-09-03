# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: contacts

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from pos.models import Company, Category, Contact, Discount, Product, Price
from pos.views.util import error, JSON_response, JSON_parse, resize_image, validate_image
from common import globals as g
from common import unidecode
from common.functions import get_random_string

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
