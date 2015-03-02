# -*- coding:utf-8 -*-
import string

import django
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

import requests
from action.functions import action_to_dict
from action.models import Action
from bl_auth import User

from common.functions import JsonParse, JsonError, get_random_string, send_email, JsonOk, min_password_requirments
from common.globals import GOOGLE

from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth import login as django_login
from django.conf import settings as settings
from django.utils.translation import ugettext as _

from blusers.models import BlocklogicUser, UserImage

from config.functions import get_user_value, set_user_value
import common.globals as g
from pos.views.manage.company import company_to_dict

from settings import GOOGLE_API

from rest_framework import parsers, renderers
from rest_framework.authentication import OAuth2Authentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.views import APIView
from pos.views.manage.company import company_to_dict


def set_language(request):
    if 'session' in request:
        request.session['django_language'] = get_user_value(request.user, 'language')


def unset_language(request):
    if 'django_language' in request.session:
        del request.session['django_language']


def login(request, data):
    """ log the user in;
        if successful, redirect to the index page
        if not successful, redirect back to the login page

        this is not a view!.
    """
    next = ''

    username = data.get('email')
    password = data.get('password')

    if request.GET.get('next', '') != '':
        next = request.GET.get('next')

    if request.POST.get('next', '') != '':
        next = request.POST.get('next')

    if User.exists(username) and User.type(username) == "google":
        return 'registered-with-google', next

    user = django_authenticate(username=username, password=password)

    if user is not None:
        # log in
        django_login(request, user)
        # activate this user's language
        set_language(request)
        message = "logged-in"
    else:
        # error page: wrong name/password
        message = "login-failed"

    # lets try google
    if message == 'login-failed':
        try:
            user = BlocklogicUser.objects.get(username=username, type=GOOGLE)
            message = 'google-login'
        except BlocklogicUser.DoesNotExist:
            pass

    # if still failing, lets see if user is not activated
    if message == 'login-failed':
        try:
            user = BlocklogicUser.objects.get(username=username, is_active=False)
            message = 'user-inactive'
        except BlocklogicUser.DoesNotExist:
            pass

    return message, next


def google_login_or_register(request, mobile=False):
    """ log the user in;
        if successful, redirect to the index page
        if not successful, redirect back to the login page """
    context = {}

    d = JsonParse(request.POST.get('data'))
    if "access_token" not in d:
        return JsonError("no_access_token", _("No access_token provided."))

    url = (GOOGLE_API['client_userinfo'] % d["access_token"])
    r = requests.get(url)

    if mobile:
        if r is None:
            return {'status': 'error', 'google_api_error': _("Something went wrong.")}
        if r.status_code == 401:
            return {'status': 'error', 'invalid_token': _("Token is invalid")}
        elif r.status_code != 200:
            return {'status': 'error', 'google_api_error': _("Something went wrong.")}
    else:
        if r is None:
            return JsonError("google_api_error", _("Something went wrong."))
        if r.status_code != 200:
            return JsonError("google_api_error", _("Something went wrong."))


    r = r.json()

    if "error" in r:
        return JsonError("google_api_error", _("Something went wrong."))
    if not "email" in r and r['email'] != "":
        if mobile:
            return {'status': 'error', 'google_api_error': _("Something went wrong.")}
        else:
            return JsonError("google_api_error", _("Something went wrong."))

    try:
        bluser = BlocklogicUser.objects.get(email=r["email"])

        if bluser.first_name != r["given_name"] or bluser.last_name != r["family_name"] or bluser.sex != r["gender"]:
            bluser.first_name = r["given_name"]
            bluser.last_name = r["family_name"]
            bluser.sex = r["gender"]
            bluser.save()

            bluser.update_user_profile()

        if bluser.type != GOOGLE and not mobile:
            return JsonError("already_registered_via_normal", _("Already registered via normal"))
        elif bluser.type != GOOGLE and mobile:
            return {'status': 'error', 'already_registered_via_normal': _("Already registered via normal")}

    except BlocklogicUser.DoesNotExist:
        # we do not have user in our db, so we add register/new one
        # print r
        try:
            gender = r["gender"]
        except KeyError:
            gender = g.MALE

        bluser = BlocklogicUser(email=r["email"], first_name=r["given_name"], last_name=r["family_name"], sex=gender,
                                type="google")
        bluser.save()

        key = ""
        while key == "":
            key = get_random_string(15, string.lowercase + string.digits)
            user = BlocklogicUser.objects.filter(password_reset_key=key)

            if user:
                key = ""

        bluser.password_reset_key = key
        bluser.save()

        bluser.update_user_profile()

        group = bluser.homegroup

        # add_free_subscription(bluser)

    user = django_authenticate(username=r["email"], password='', type=GOOGLE)

    if user is not None:
        if not mobile:
            django_login(request, user)
            set_user_value(bluser, 'google_access_token', d["access_token"])
            set_language(request)

        group = user.homegroup

        data = {'status': 'ok', 'redirect_url': reverse('web:home', kwargs={'group_id': group.id, 'section': 'home'}), 'user_id': user.id}

        if len(user.images.all()) == 0:
            picture_url = r['picture']
            r = requests.get(picture_url, stream=True)

            if r.status_code == 200:
                original_filename = picture_url.rsplit('/', 1)

                user_image = UserImage(name=user.first_name + " " + user.last_name, original_filename=original_filename[1], created_by=user, updated_by=user)
                user_image.image.save(original_filename[1], ContentFile(r.raw.read()))
                user_image.save()

                user.images.add(user_image)
                user.save()

        if mobile:
            return data

        return JsonResponse(data)

    return JsonError("error", _("Something went wrong during login with google"))


def try_register(user_form):
    new_user = user_form.save()
    new_user.set_password(user_form.cleaned_data['password1'])

    key = ""
    while key == "":
        key = get_random_string(15, string.lowercase + string.digits)
        user = BlocklogicUser.objects.filter(password_reset_key=key)

        if user:
            key = ""

    new_user.password_reset_key = key
    new_user.type = 'normal'
    new_user.is_active = False
    new_user.save()
    new_user.update_user_profile()

    # TODO: add the free subscription on register
    # add_free_subscription(new_user)

    activation_url = reverse('web:activate_account', args={key})

    # put the stuff in template, then render it to string and send it via email
    mail_context = {
        'url': settings.SITE_URL + activation_url,
        'site_url': settings.SITE_URL,
    }

    subject = settings.EMAIL_SUBJECT_PREFIX + " " + _("Registration successful")

    message_html = render_to_string('email/email_verification.html', mail_context)
    message_text = render_to_string('email/email_verification.txt', mail_context)

    if settings.DEBUG:
        print message_text
        print message_html
    else:
        send_email(settings.EMAIL_FROM, [new_user.email], None, subject, message_text, message_html)


def send_reactivation_key(request, bluser):
    """
    This is not a view, just normal function used in lost_password view.

    First we get unique key for user profile, then send mail with unique
    reactivation key.
    """

    # we need unique key
    def create_key():
        # 15: defined in BlocklogicUser model (password_reset_key)
        return get_random_string(15, string.lowercase + string.digits)

    key = create_key()
    while BlocklogicUser.objects.filter(password_reset_key=key).count() > 0:
        key = create_key()

    bluser.password_reset_key = key
    bluser.save()

    # render a message from template and send it to email
    reactivation_url = reverse('web:recover_password', args={key})

    # put the stuff in template, then render it to string and send it via email
    mail_context = {
        'url': settings.SITE_URL + reactivation_url,
        'site_url': settings.SITE_URL,
    }

    subject = settings.EMAIL_SUBJECT_PREFIX + " " + _("Recover lost password")

    message_html = render_to_string('email/lost_password.html', mail_context)
    message_text = render_to_string('email/lost_password.txt', mail_context)

    if settings.DEBUG:
        print "sending register email"
        print message_text
        print message_html
    else:
        send_email(settings.EMAIL_FROM, [bluser.email], None, subject, message_text, message_html)



def get_user_credentials(user):
    credentials = {}

    credentials['user_id'] = user.id
    credentials['user_email'] = user.email
    credentials['user_first_name'] = user.first_name
    credentials['user_last_name'] = user.last_name
    # credentials['other_groups'] = groups_to_dict(user.user_groups, user, participant=True)

    """
    try:
        up = UserProfile.objects.get(user=user)

        credentials['is_company'] = True
        credentials['company_name'] = up.company_name
        credentials['company_address'] = up.company_address
        credentials['company_city'] = up.company_city
        credentials['company_postcode'] = up.company_postcode
        credentials['company_tax_id'] = up.company_tax_id
        credentials['company_tax_payer'] = up.company_tax_payer

        if up.company_country:
            credentials['company_country'] = up.company_country.two_letter_code

    except UserProfile.DoesNotExist:
        credentials['is_company'] = False
        pass
    """

    return credentials


def get_actions(user):
    # companies = user.companies

    # the list of messages
    actions = Action.objects.filter(status=g.ACTION_WAITING, receiver=user.email)

    data = []
    for a in actions:
        data.append(action_to_dict(user, a, android=True))

    return data


class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer
    authentication_classes = (OAuth2Authentication, TokenAuthentication,)
    model = Token

    def post(self, request, backend):

        if backend == 'auth':
            if request.META and 'HTTP_AUTHORIZATION' in request.META:
                user = get_user(request)
            else:
                serializer = self.serializer_class(data=request.DATA)
                if serializer.is_valid():
                    user = serializer.object['user']
                else:
                    return JsonError(message=_("wrong credentials"))

        elif backend == "google-oauth2":
            d = google_login_or_register(request, mobile=True)
            if d['status'] == 'ok':
                user = BlocklogicUser.objects.get(id=d['user_id'])
            else:
                return JsonResponse(d)

        else:
            return JsonError(message=_("wrong login"))

        token, created = Token.objects.get_or_create(user=user)

        if user:
            user_credentials = get_user_credentials(user)
        else:
            return JsonError(_("User authentication failed."))

        companies = user.companies
        actions = get_actions(user)

        return JsonResponse({'token': token.key,
                             'user': user_credentials,
                             'actions': actions,
                             'companies': [company_to_dict(user, i, android=True, with_config=True) for i in companies],
                             'status': "ok"})
obtain_auth_token = ObtainAuthToken.as_view()


def get_user(request):
    if request.user.is_authenticated():
        return request.user
    else:
        return None



