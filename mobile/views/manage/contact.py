from django.utils.translation import ugettext as _

from pos.models import Company, Contact
from common import globals as g
from config.functions import get_date_format, get_user_value
from pos.views.manage.contact import contact_to_dict, get_contact, validate_contact
from pos.views.util import JSON_response, JSON_ok, JSON_parse, JSON_error, has_permission, no_permission_view

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_list_contacts(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'contact', 'view'):
        return JSON_error(_("You have no permission to view products"))

    contacts = Contact.objects.filter(company__id=c.id)

    criteria = JSON_parse(request.POST['data'])
    cs = []
    for contact in contacts:
        cs.append(contact_to_dict(request.user, c, contact, "android"))

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
        return JSON_error("type cannot be None Stupid")

    contact = Contact(
        company=c,
        created_by=request.user,
        type=type,
        company_name=data.get('company_name'),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        sex=data.get('sex'),
        date_of_birth=data.get('date_of_birth'),
        street_address=data.get('street_address'),
        postcode=data.get('postcode'),
        city=data.get('city'),
        state=data.get('state'),
        country=data.get('country'),
        email=data.get('email'),
        phone=data.get('phone'),
        # vat = data['vat']
    )
    contact.save()

    return JSON_ok(extra=contact_to_dict(request.user, c, contact, send_to="android"))

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_contact(request, company):

    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    #contact_id = request.POST.get('contact_id')
    #print contact_id
    # sellers can edit product
    if not has_permission(request.user, c, 'product', 'edit'):
        return JSON_error(_("You have no permission to edit products"))

    data = JSON_parse(request.POST['data'])
    contact_id = data.get('id')

    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return JSON_error(_("Contact doest not exist"))

    valid = validate_contact(request.user, c, data)
    if not valid['status']:
        return JSON_error(valid['messege'])

    data = valid['data']

    contact.company = c
    contact.created_by = request.user
    contact.type = data.get('type')
    contact.company_name = data.get('company_name')
    contact.first_name = data.get('first_name')
    contact.last_name = data.get('last_name')
    contact.sex = data.get('sex')
    contact.date_of_birth = data.get('date_of_birth')
    contact.street_address = data.get('street_address')
    contact.postcode = data.get('postcode')
    contact.city = data.get('city')
    contact.state = data.get('state')
    contact.country = data.get('country')
    contact.email = data.get('email')
    contact.phone = data.get('phone')
    # contact.vat = data['vat']

    contact.save()

    return JSON_ok(extra=contact_to_dict(request.user, c, contact))
    

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_contact(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'contact', 'edit'):
        return no_permission_view(request, c, _("delete contacts"))

    data = JSON_parse(request.POST['data'])
    contact_id = data.get('id')

    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return JSON_error(_("Contact does not exist"))

    contact.delete()

    return JSON_ok(extra=contact_to_dict(request.user, c, contact))
