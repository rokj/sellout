from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from action.models import Action
from blusers.models import BlocklogicUser
from common.functions import send_email
from decorators import login_required

from pos.models import Company, Permission
import common.globals as g
from pos.views.util import JsonError, JsonParse, has_permission, JsonOk

import json
import settings


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

    # TODO: finish the shiat


@login_required
def invite_user(request, company):
    """ create a new Action entry """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company not found"))

    # permissions
    if not has_permission(request.user, c, 'user', 'edit'):
        return JsonError(_("You have no permissions to invite users"))

    # data:
    # emails is a list of dictionaries:
    # {'email': 'asdf@example.com', 'permission': 'cashier'}
    try:
        data = JsonParse(request.POST.get('data'))
        if not data:
            raise KeyError
    except (ValueError, AttributeError, TypeError, KeyError):
        return JsonError(_("No data in request"))

    # requested data:
    errors = []
    valid_data = []

    for d in data:
        email = d.get('email')
        if not email:
            continue

        # validate permission
        permission = d.get('permission')
        if permission not in g.PERMISSION_TYPES:
            # this shouldn't happen, don't even translate
            errors.append("This permission type is not valid: " + email + ": " + permission)

        # validate this email
        try:
            validate_email(email)
            valid_data.append(d)
        except ValidationError:
            errors.append(email)

        # check if this user is already a member of this company
        if Permission.objects.get(company=c, user__email=email).exists():
            errors.append(_("User with this email is already member of the group: ") + email)

    if len(errors) > 0:
        return JsonError(errors)

    # insert all emails as Actions
    for d in valid_data:
        email = d.get('email')
        permission = d.get('permission')

        # delete any waiting actions from the same company and for the same user;
        Action.objects.filter(company=c, receiver=email, type=g.ACTION_INVITATION, status=g.ACTION_WAITING).delete()

        # create new Action entries
        action_data = {"user_email": request.user.email,
                       "user_first_last_name": str(request.user),
                       "permission": permission}

        action = Action(
            created_by=request.user,
            company=c,
            sender=request.user.email,
            receiver=email,
            type=g.ACTION_INVITATION,
            status=g.ACTION_WAITING,
            data=json.dumps(action_data)
        )
        action.save()

        # send a different invite to non-registered users and registered users
        if BlocklogicUser.objects.get(email=email).exists():
            template_html = 'email/invitation_for_registered_users.html'
            template_text = 'email/invitation_for_registered_users.txt'
        else:
            template_html = 'email/invitation_for_non_registered_users.html'
            template_text = 'email/invitation_for_non_registered_users.txt'

        # send email
        mail_context = {
            'company_name': c.name,
            'register_url': settings.SITE_URL + reverse('web:sign_up'),
            'login_url': settings.SITE_URL + reverse('web:login'),
        }

        message_html = render_to_string(template_html, mail_context)
        message_text = render_to_string(template_text, mail_context)

        if settings.DEBUG:
            print message_text
            print "============="
            print message_html
        else:
            send_email(settings.EMAIL_FROM, [email], None, _("Invitation to join company on Sellout.biz"),
                       message_text, message_html)

    return JsonOk()