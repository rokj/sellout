import json
import urllib
from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.http import JsonResponse, QueryDict
from django.shortcuts import redirect, render
from bl_auth import User
from blusers.forms import LoginForm, BlocklogicUserForm, ResetPasswordForm, BlocklogicUserChangeForm
from django.utils.translation import ugettext as _
from blusers.models import BlocklogicUser
from blusers.views import try_register, unset_language, send_reactivation_key
from django.contrib.auth.decorators import login_required as login_required_nolocking, login_required
from django.contrib.auth import logout as django_logout
from action.models import Action
from common.functions import send_email, JSON_parse, JsonOk, min_password_requirments, JSON_error, JSON_ok
from django.contrib.auth import authenticate as django_authenticate


import common.globals as g
from config.functions import get_user_value, set_user_value
from pos.models import Permission

import settings


def index(request):
    message = None
    next = None
    action = ''

    # if the user is already logged in, redirect to select_company
    if request.user.is_authenticated():
        return redirect('web:select_company')

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
        'user': request.user,
        'action': action,
        'next': next,
        'login_message': message,
        'login_form': login_form,
        'client_id': settings.GOOGLE_API['client_id'],
        'site_title': g.SITE_TITLE,
        'STATIC_URL': settings.STATIC_URL,
        'GOOGLE_API': settings.GOOGLE_API,
        'SITE_URL': settings.SITE_URL
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
                    return sign_up_message(request, 'user-exists-google')
                elif User.type(email) == "normal":
                    return sign_up_message(request, 'user-exists-normal')
                else:
                    return sign_up_message(request, 'user-exists')

            # common function with mobile
            try_register(user_form)

            # registration succeeded, return to login page
            return sign_up_message(request, 'registration-successful')
        else:
            print user_form.errors.as_data()
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
        'site_title': g.SITE_TITLE,
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


def handle_invitation(request, reference, user_response, mobile=False):
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
        # new_permission.create_pin(False)
        new_permission.save()

    # else: if the invite was declined, just update its status (which must be done anyway)
    action.status = user_response
    action.save()
    if mobile:
        return JsonOk()
    else:
        return redirect('web:select_company')


@login_required_nolocking
def accept_invitation(request, reference, mobile=False):
    return handle_invitation(request, reference, g.ACTION_ACCEPTED, mobile=mobile)



@login_required_nolocking
def decline_invitation(request, reference, mobile=False):
    return handle_invitation(request, reference, g.ACTION_DECLINED, mobile=mobile)


@login_required_nolocking
def user_profile(request):
    user = BlocklogicUser.objects.get(email=request.user.email)

    if request.method == 'POST':
        my_dict = {
            'country': request.POST['country'],
            'first_name': user.first_name,
            'last_name': request.POST['last_name'],
            'sex': user.sex
        }

        query_string = urllib.urlencode(my_dict)
        query_dict = QueryDict(query_string)

        user_form = BlocklogicUserChangeForm(query_dict)
        user_form.set_request(request)

        if user_form.is_valid():
            user.last_name = my_dict['last_name']
            user.country = my_dict['country']
            user.save()
        else:
            user_form = BlocklogicUserChangeForm(initial={'last_name': my_dict['last_name'], 'country': my_dict['country']})
    else:
        user_form = BlocklogicUserChangeForm(initial={'last_name': user.last_name, 'country': user.country})

    context = {
        'user_form': user_form,
        'user': user
    }

    return render(request, 'web/user_profile.html', context)

def send_contact_message(request):
    if not request.is_ajax():
        return JsonResponse({
                'status': 'not_ajax',
        })

    d = JSON_parse(request.POST.get('data'))

    if not d:
        return JsonResponse({'status': 'error', 'message': _("No data in request")})

    if "email" not in d:
        return JsonResponse({
                'status': 'no_email',
        })

    if "first_last_name" not in d:
        return JsonResponse({
                'status': 'no_first_name',
        })

    if "message" not in d:
        return JsonResponse({
                'status': 'no_message',
        })

    try:
        validate_email(d.get('email'))
    except ValidationError:
        return JsonResponse({
                'status': 'not_valid_email',
        })

    subject = _('Message from') + " " + settings.SITE_URL
    message = d.get('message')

    message_html = message.replace("\r\n", "<br />")
    message_html = message_html.replace("\n", "<br />")
    message_html = message_html + "<br /><br />"
    message_html = message_html + _("Message was sent by:") + " " + d.get('first_last_name')

    if settings.DEBUG:
        print "We are sending email with subject:"
        print subject
        print "and message:"
        print "--- text ---"
        print message
        print "--- text ---"
        print "--- html ---"
        print message_html
        print "--- html ---"
    else:
        send_email(d.get('email'), [settings.CONTACT_EMAIL], None, subject, message, message_html)

    return JsonResponse({
            'status': 'ok'
    })

def supported_hardware(request):
    return render(request, 'web/supported_hardware.html')

def faq(request):
    return render(request, 'web/faq.html')

def robots(request):
    return render(request, 'web/robots.txt', content_type='text/plain')


@login_required
def update_password(request):
    if not request.method == 'POST':
        return JSON_error("error")

    d = JSON_parse(request.POST.get('data'))

    if 'current_password' not in d or 'password1' not in d or 'password2' not in d:
        return JSON_error('error', _('Something went wrong during password saving. Contact support.'))

    if d['password1'] != d['password2']:
        return JSON_error('new_password_mismatch', _('New passwords do not match'))

    if not min_password_requirments(d['password1']):
        return JSON_error('min_pass_requirement_failed', _('Password minimal requirments failed.'))

    user = django_authenticate(username=request.user.email, password=d['current_password'])
    if user is None:
        return JSON_error('wrong_current_password')

    if user is not None:
        # saves in django table
        user.set_password(d['password1'])
        user.save()

        user.update_user_profile()

        return JSON_ok()

    return JSON_error('error', _('Something went wrong during password saving. Contact support.'))

def redirect_page(request):
    url = request.GET['url']

    return redirect(url)