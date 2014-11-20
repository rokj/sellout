
from django.utils.translation import ugettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Register, Company
from pos.views.manage.register import get_all_registers, validate_register, register_to_dict
from pos.views.util import has_permission, manage_delete_object, JsonOk, JsonError, JsonParse


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_register(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    user = request.user

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'register', 'view'):
        return JsonError(_("You have no permission to view registers"))

    data = JsonParse(request.POST['data'])
    device_id = data['device_id']

    print device_id

    try:
        register = Register.objects.get(company=c, device_id=device_id)
        r = {
            'register': register_to_dict(request.user, c, register)
        }
    except Register.DoesNotExist:
        r = {
            'register': None
        }

    return JsonOk(extra=r, safe=False)



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_add_register(request, company):
    # add a new register
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'register', 'edit'):
        return JsonError(_("You have no permission to edit registers"))

    data = JsonParse(request.POST['data'])
    print data
    valid = validate_register(request.user, c, data)

    if not valid.get('status'):
        return JsonError(valid['message'])

    form = valid['form']
    register = form.save(False)
    register.company = c
    register.created_by = request.user
    register.device_id = data['device_id']

    register.save()

    return JsonOk(extra=register_to_dict(request.user, company, register))


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_edit_register(request, company):
    # add a new register
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'register', 'edit'):
        return JsonError(_("You have no permission to edit registers"))

    data = JsonParse(request.POST['data'])

    try:
        register = Register.objects.get(id=int(data['id']), company=c)
    except Register.DoesNotExist:
        return JsonError(_("Register does not exists"))

    valid = validate_register(request.user, c, data, register=register)

    if not valid.get('status'):
        return JsonError(valid['message'])

    form = valid['form']
    register = form.save(False)
    register.company = c
    register.created_by = request.user
    register.device_id = data['device_id']

    register.save()

    return JsonOk(extra=register_to_dict(request.user, c, register))

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_delete_register(request, company):
    return manage_delete_object(request, company, Register,
                                (_("You have no permission to delete registers"), _("Could not delete register")))

