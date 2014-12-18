from django.http import JsonResponse
from django.utils.translation import ugettext as _

from pos.models import Company, Contact
from common import globals as g
from config.functions import get_date_format, get_user_value
from pos.views.manage.contact import contact_to_dict, get_contact, validate_contact
from common.functions import JsonOk, JsonParse, JsonError, has_permission, no_permission_view

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_list_contacts(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'contact', 'view'):
        return JsonError(_("You have no permission to view products"))

    contacts = Contact.objects.filter(company=c)

    criteria = JsonParse(request.POST['data'])
    cs = []
    for contact in contacts:
        cs.append(contact_to_dict(request.user, c, contact))

    return JsonResponse(cs, safe=False)



@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_get_contact(request, company, contact_id):
    return get_contact(request, company, contact_id)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_add_contact(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # sellers can add product
    if not has_permission(request.user, c, 'product', 'edit'):
        return JsonError(_("You have no permission to add products"))

    data = JsonParse(request.POST['data'])

    # validate data
    valid = validate_contact(request.user, c, data)
    if not valid['status']:
        return JsonError(valid['message'])
    data = valid['data']

    if 'type' in data:
        type = data['type']
    else:
        return JsonError("type cannot be None Stupid")

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
        vat=data.get('vat')
    )
    contact.save()

    return JsonOk(extra=contact_to_dict(request.user, c, contact))

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_contact(request, company_id):

    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # sellers can edit product
    if not has_permission(request.user, c, 'product', 'edit'):
        return JsonError(_("You have no permission to edit products"))

    data = JsonParse(request.POST['data'])
    contact_id = data.get('id')

    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return JsonError(_("Contact doest not exist"))

    valid = validate_contact(request.user, c, data)
    if not valid['status']:
        return JsonError(valid['messege'])

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
    contact.vat = data['vat']

    contact.save()

    return JsonOk(extra=contact_to_dict(request.user, c, contact))
    

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_contact(request, company_id):
    try:
        c = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'contact', 'edit'):
        return no_permission_view(request, c, _("delete contacts"))

    data = JsonParse(request.POST['data'])
    contact_id = data.get('id')

    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        return JsonError(_("Contact does not exist"))

    contact.delete()

    return JsonOk(extra=contact_to_dict(request.user, c, contact))
