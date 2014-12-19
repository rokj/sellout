import json
from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import redirect, render
from bl_auth import User
from blusers.forms import LoginForm, BlocklogicUserForm, ResetPasswordForm
from django.utils.translation import ugettext as _
from blusers.models import BlocklogicUser
from blusers.views import try_register, unset_language, send_reactivation_key
from django.contrib.auth.decorators import login_required as login_required_nolocking
from django.contrib.auth import logout as django_logout
from action.models import Action

import common.globals as g
from config.functions import get_user_value, set_user_value
from pos.models import Permission

import settings


def index(request):
    message = None
    next = None

    action = ''

    if request.method == 'POST':
        action = 'login'

        if request.POST.get('next', '') != '':
            next = request.POST.get('next')

        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            from blusers.views import login
            message, next = login(request, login_form.cleaned_data)

            if message == 'logged-in':
                return redirect('web:select_company')
    else:
        login_form = LoginForm()

    if request.GET.get('next') != '' and request.GET.get('next') != reverse('web:logout'):
        next = request.GET.get('next')

    context = {
        'action': action,
        'next': next,
        'login_message': message,
        'login_form': login_form,
        'client_id': settings.GOOGLE_API['client_id'],
        'title': "",
        'site_title': g.SITE_TITLE,
        'STATIC_URL': settings.STATIC_URL,
        'GOOGLE_API': settings.GOOGLE_API
    }

    return render(request, "web/index.html", context)


@login_required_nolocking
def select_company(request):
    """ show current user's companies and a list of invites. """

    # the list of companies
    companies = request.user.companies

    # the list of messages
    actions = Action.objects.filter(status=g.ACTION_WAITING, receiver=request.user.email)

    for a in actions:
        if a.type == g.ACTION_INVITATION:
            a.data = json.loads(a.data)

            a.accept_url = settings.SITE_URL + reverse('web:accept_invitation', args=[a.reference])
            a.decline_url = settings.SITE_URL + reverse('web:decline_invitation', args=[a.reference])

    context = {
        'title': _("Select company"),
        'site_title': g.SITE_TITLE,

        'companies': companies,
        'actions': actions,
    }

    return render(request, "web/select_company.html", context)


def sign_up_message(request, message_code):
    context = {
        'site_title': g.SITE_TITLE,
        'message_code': message_code,
    }

    return render(request, 'web/sign_up_message.html', context)


def sign_up(request):
    if request.method == 'POST':
        user_form = BlocklogicUserForm(request.POST)
        user_form.set_request(request)

        if user_form.is_valid():
            email = user_form.cleaned_data['email']

            if User.exists(email):
                if User.type(email) == "google":
                    sign_up_message(request, 'user-exists-google')
                elif User.type(email) == "normal":
                    sign_up_message(request, 'user-exists-normal')
                else:
                    return sign_up_message(request, 'user-exists')

            # common function with mobile
            try_register(user_form)

            # registration succeeded, return to login page
            return sign_up_message(request, 'registration-successful')
    else:
        user_form = BlocklogicUserForm()

    next = None
    if request.GET.get('next') and request.GET.get('next') != reverse('logout'):
        next = request.GET.get('next')

    context = {
        'next': next,
        'user_form': user_form,
        'client_id': settings.GOOGLE_API['client_id'],
        'title': _("Sign up"),
        'GOOGLE_API': settings.GOOGLE_API
    }

    return render(request, 'web/sign_up.html', context)



@login_required_nolocking
def logout(request):
    context = {
        'google_account': False
    }

    if request.user and request.user.type == g.GOOGLE:
        context['google_account'] = True
        context['GOOGLE_API'] = settings.GOOGLE_API

        # try:
            # google_access_token = get_value(request.user, 'google_access_token')
            # url = ('https://accounts.google.com/o/oauth2/revoke?token=%s' % google_access_token)

            # r = requests.get(url)
            # if r.status_code == 200:

        # except InvalidKeyError:
        #    pass

    django_logout(request)
    unset_language(request)

    return redirect('web:index')


def activate_account(request, key):
    """ if activation is successful: go to the 'enter' page with message='activation-successful'
        otherwise, message is 'activation-failed'
    """
    if request.user.is_authenticated():
        return redirect('web:index')

    try:
        user = BlocklogicUser.objects.get(password_reset_key=key)
        user.is_active = True
        user.save()

        message = 'activation-successful'
    except BlocklogicUser.DoesNotExist:
        message = 'activation-failed'

    return sign_up_message(request, message)


def lost_password(request):
    def render_return(message):
        context = {
            'message': message,

            'site_title': g.SITE_TITLE,
            'title': _("Lost password"),
        }

        return render(request, 'web/lost_password.html', context)

    if request.method == 'POST':
        if "email" in request.POST:
            try:
                validate_email(request.POST["email"])
            except ValidationError:
                return render_return(_("Invalid e-mail"))

            try:
                bluser = BlocklogicUser.objects.get(email=request.POST["email"])
                if bluser.type == g.GOOGLE:
                    return render_return(_("You have registered with google account. "
                                           "Try signing in by clicking on 'google login' button in login form."))

                send_reactivation_key(request, bluser)

                return render_return(_("Your password reset key has been sent to your e-mail, "
                                       "please check your inbox."))

            except BlocklogicUser.DoesNotExist:
                return render_return(_("A user with this e-mail does not exist"))

        return render_return(_("Unknown error occured. Please contact support."))
    else:
        return render_return(None)


def recover_password(request, key):
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)

        if form.is_valid():
            # passwords are the same
            password = form.cleaned_data['new_password_1']

            print password

            # reset key has been checked in form validation
            bluser = BlocklogicUser.objects.get(password_reset_key=key)
            bluser.set_password(password)
            bluser.password_reset_key = None
            bluser.save()
            bluser.update_password()

            return redirect('web:index')
    else:
        form = ResetPasswordForm(initial={'key': key})

    context = {
        'title': _("Recover lost password"),
        'site_title': g.SITE_TITLE,

        'form': form,
        'key': key,
    }

    return render(request, 'web/recover_password.html', context)


def handle_invitation(request, reference, user_response):
    try:
        action = Action.objects.get(receiver=request.user.email,
                                    reference=reference,
                                    status=g.ACTION_WAITING)
    except Action.DoesNotExist:  # wtf?
        return redirect('web:select_company')

    # if the invite has been accepted, create a new permission
    if user_response == g.ACTION_ACCEPTED:
        data = json.loads(action.data)
        permission = data.get('permission')
        if permission not in g.PERMISSION_TYPES:
            permission = g.PERMISSION_TYPES[0]

        # get the user that sent the invite and select it as the user that created the permission
        try:
            sender = BlocklogicUser.objects.get(email=action.sender)
        except BlocklogicUser.DoesNotExist:
            sender = request.user

        new_permission = Permission(
            created_by=sender,
            user=request.user,
            company=action.company,
            permission=permission
        )
        new_permission.create_pin(False)
        new_permission.save()

    # else: if the invite was declined, just update its status (which must be done anyway)
    action.status = user_response
    action.save()

    return redirect('web:select_company')


@login_required_nolocking
def accept_invitation(request, reference):
    return handle_invitation(request, reference, g.ACTION_ACCEPTED)



@login_required_nolocking
def decline_invitation(request, reference):
    return handle_invitation(request, reference, g.ACTION_DECLINED)


@login_required_nolocking
def user_profile(request):
    context = {

    }

    return render(request, 'web/user_profile.html', context)