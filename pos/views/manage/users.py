from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from decorators import login_required

from pos.models import Company, Permission
import common.globals as g
from pos.views.util import JsonError, JsonParse, has_permission, JsonOk, manage_delete_object


@login_required
def list_users(request, company):
    """ show a list of users and their pins """
    c = get_object_or_404(Company, url_name=company)

    permissions = Permission.objects.filter(company=c)

    context = {
        'company': c,
        'permissions': permissions,
        'permission_groups': g.PERMISSION_GROUPS,

        'title': _("Discounts"),
        'site_title': g.MISC['site_title'],
    }

    return render(request, 'pos/manage/users.html', context)


@login_required
def edit_permission(request, company):
    """ receive a JSON with fields: permission_id, permission, pin """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # get data
    try:
        d = JsonParse(request.POST.get('data'))
        if not d:
            raise KeyError
    except (ValueError, AttributeError, TypeError, KeyError):
        return JsonError(_("No data in request"))


    # check for permission:
    if not has_permission(request.user, c, 'user', 'edit'):
        return JsonError(_("You have no permission to edit users"))

    # get the permission
    try:
        permission = Permission.objects.get(id=int(d.get('permission_id')), company=c)
    except (ValueError, Permission.DoesNotExist):
        return JsonError(_("This user does not exist"))

    # check the data
    if d.get('permission') not in g.PERMISSION_TYPES:
        return JsonError(_("This permission type does not exist"))

    # everything seems to be OK, update PIN
    if not permission.create_pin(int(d.get('pin'))):
        return JsonError(_("This PIN has already been assigned to a user from this company."
                           "Please choose a different PIN."))

    # update permission
    permission.permission = d.get('permission')
    permission.save()

    # ok!
    return JsonOk()


@login_required
def delete_permission(request, company):
    """ remove the user from this company """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company not found"))

    if not has_permission(request.user, c, 'user', 'edit'):
        return JsonError(_("You have no permissions to remove users"))

    # id is in request.POST in JSON format
    try:
        permission = Permission.objects.get(int(JsonParse(request.POST.get('data')).get('permission_id')), company=c)

    except (Permission.DoesNotExist, ValueError):
        return JsonError(_("The user does not exist"))

