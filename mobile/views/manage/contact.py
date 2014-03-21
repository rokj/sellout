from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from pos.models import Company, Contact
from common import globals as g
from config.functions import get_date_format, get_value
from pos.views.manage.contact import contact_to_dict, get_contact, validate_contact
from pos.views.util import JSON_response, JSON_ok, JSON_parse, JSON_error, has_permission, no_permission_view, format_date,\
    max_field_length, parse_date

from rest_framework.decorators import api_view, permission_classes,\
    authentication_classes
from rest_framework.permissions import IsAuthenticated
from config.models import Country

import re



@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_list_contacts(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'contact', 'list'):
        return JSON_error(_("You have no permission to view products"))

    contacts = Contact.objects.filter(company__id=c.id)

    criteria = JSON_parse(request.POST['data'])
    cs = []
    for c in contacts:
        cs.append(contact_to_dict(request.user, c, "android"))

    print JSON_response(cs)
    return JSON_response(cs)



@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_get_contact(request, company, contact_id):
    return get_contact(request, company, contact_id)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_add_contact(request, company):
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

    if 'type' in data:
        type = data['type']
    else:
        type = None



    contact = Contact(
        company = c,
        created_by = request.user,
        type = type,
        company_name = data['company_name'] if 'company_name' in data else None,
        first_name = data['first_name'] if 'first_name' in data else None,
        last_name = data['last_name'] if 'last_name' in data else None,
        sex = data['sex'] if 'sex' in data else None,
        date_of_birth = data['date_of_birth'] if 'date_of_birth' in data else None,
        street_address = data['street_address'] if 'street_address' in data else None,
        postcode = data['postcode'] if 'postcode' in data else None,
        city = data['city'] if 'city' in data else None,
        state = data['state'] if 'state' in data else None,
        country = data['country'] if 'country' in data else None,
        email = data['email'] if 'email' in data else None,
        phone = data['phone'] if 'phone' in data else None,
        #vat = data['vat']
    )
    contact.save()

    return JSON_ok(extra=contact_to_dict(request.user, contact, send_to="android"))

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_contact(request, company, contact_id):
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
    print valid
    if not valid['status']:
        return JSON_error(valid['messege'])

    data = valid['data']
    c = get_object_or_404(Company, url_name=company)

    contact.company = c
    contact.type = data['type']
    contact.company_name = data['company_name']
    contact.first_name = data['first_name']
    contact.last_name = data['last_name']
    contact.sex = data['sex']
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
    

def mobile_delete_contact(request, company, contact_id):
    # TODO
    return JSON_ok()
