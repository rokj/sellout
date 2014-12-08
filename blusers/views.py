# -*- coding:utf-8 -*-
import base64
import string
import json
import django
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.template.loader import render_to_string
import requests
from rest_framework import parsers, renderers
from rest_framework.authentication import OAuth2Authentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.views import APIView
from action.models import Action
from bl_auth import User
from common.functions import JsonParse, JsonError, get_random_string, send_email, JsonOk, min_password_requirments
from common.globals import GOOGLE
from common.views import base_context
from common.globals import WAITING

from common.decorators import login_required
from django.core.files.base import ContentFile
from django.http import Http404, QueryDict, JsonResponse
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth import login as django_login
from django.shortcuts import render, redirect
from django.conf import settings as settings
from django.utils.translation import ugettext as _


from blusers.forms import BlocklogicUserForm, BlocklogicUserChangeForm
from blusers.models import BlocklogicUser, UserImage
import common.globals as g
from config.functions import get_user_value, set_user_value, get_company_config

from rest_framework.decorators import api_view
from mobile.views.manage.configuration import get_mobile_config, company_config_to_dict
from pos.models import Company
from settings import GOOGLE_API

from easy_thumbnails.files import get_thumbnailer

import config.countries as countries


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
        if bluser.type != GOOGLE and not mobile:
            return JsonError("already_registered_via_normal", _("Already registered via normal"))
        elif bluser.type != GOOGLE and mobile:
            return {'status': 'error', 'already_registered_via_normal': _("Already registered via normal")}

    except BlocklogicUser.DoesNotExist:
        # we do not have user in our db, so we add register/new one
        # print r

        bluser = BlocklogicUser(email=r["email"], first_name=r["given_name"], last_name=r["family_name"], sex=r["gender"],
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


def try_register(user_form, user_profile_form=None):
    """ this is not a view """
    new_user = user_form.save()
    new_user.set_password(user_form.cleaned_data['password1'])

    if user_profile_form:
        user_profile = user_profile_form.save(commit=False)
        user_profile.user = new_user
        user_profile.created_by = new_user
        user_profile.save()

    key = ""
    while key == "":
        key = get_random_string(15, string.lowercase + string.digits)
        user = BlocklogicUser.objects.filter(password_reset_key=key)

        if user:
            key = ""

    new_user.password_reset_key = key
    new_user.type = 'normal'
    new_user.is_active = False
    #new_user.update_password(user_form.cleaned_data['password1'])
    new_user.update_password()
    new_user.save()

    # TODO: add the free subscription on register
    # add_free_subscription(new_user)

    activation_url = reverse('web:activate_account', args={key})

    # put the stuff in template, then render it to string and send it via email
    mail_context = {
        'url': settings.SITE_URL + activation_url,
    }

    subject = settings.EMAIL_SUBJECT_PREFIX + " " + _("Registration successful")

    message_html = render_to_string('email/email_verification.html', mail_context)
    message_text = render_to_string('email/email_verification.txt', mail_context)

    if settings.DEBUG:
        print "sending register email"
        print message_text
        print message_html
    else:
        send_email(settings.EMAIL_FROM, [new_user.email], None, subject, message_text, message_html)


def delete_user_image(bluser, image_id):
    try:
        user_image = UserImage.objects.get(id=image_id, created_by=bluser)
        user_image.delete()

        bluser.images.filter(id=image_id).delete()

        return True
    except UserImage.DoesNotExist:
        return False


def send_reactivation_key(request, bluser):
    """
    This is not a view, just normal function used in lost_password view.

    First we get unique key for user profile, then send mail with unique
    reactivation key.
    """

    # we need unique key
    __bluser = ["ratatata"] # fake

    key = None
    while len(__bluser) > 0:
        key = get_random_string(15, string.lowercase + string.digits)
        __bluser = BlocklogicUser.objects.filter(password_reset_key=key)

    bluser.password_reset_key = key
    bluser.save()

    file = open(settings.STATIC_DIR + "email/blusers/lost-password_" + django.utils.translation.get_language() + ".txt", "r")
    message_txt = file.read()
    file.close()

    # TODO: language dependency
    #
    #if django.utils.translation.get_language() == "sl-si":
    #    reactivation_url = settings.SITE_URL.strip("/") + reverse('ponastavi_geslo', kwargs={'key': key})
    # else:
    reactivation_url = settings.SITE_URL.strip("/") + "/#recover-password=" + key

    message_txt = message_txt % (reactivation_url, settings.SITE_URL)

    reset_url = '<a href="%s">%s</a>' % (reactivation_url, reactivation_url)
    file = open(settings.STATIC_DIR + "email/blusers/lost-password_" + django.utils.translation.get_language() + ".html", "r")
    message_html = file.read()
    file.close()
    message_html = message_html % (reset_url, settings.SITE_URL)

    subject = "%s %s" % (settings.EMAIL_SUBJECT_PREFIX, unicode(_("%s - Recover password" % ("timebits.com"))))

    # TODO: remove
    if settings.DEBUG:
        print message_txt
        print "------"
        print message_html
        print "sending reactivation key"
    else:
        send_email(settings.EMAIL_FROM, [bluser.email], None, subject, message_txt, message_html)

@api_view(['POST'])
def reset_password(request):
    errors = {}
    data = JsonParse(request.POST['data'])

    if not "new_password1" in data:
        return JsonResponse({"status": "no_key"})

    if not "new_password2" in data:
        return JsonResponse({"status": "no_key"})

    if not "key" in data:
        return JsonResponse({"status": "no_key"})

    try:
        bluser = BlocklogicUser.objects.get(password_reset_key=data["key"])
    except BlocklogicUser.DoesNotExist:
        return JsonResponse({"status": "wrong_key"})

    password1 = data['new_password1']
    password2 = data['new_password2']

    if password1 != password2:
        return JsonResponse({"status": "passwords_must_be_identical"})
    else:
        bluser.set_password(password1)
        bluser.password_reset_key = None
        bluser.save()

        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "something_went_wrong"})

@login_required
def save_user_settings(request):
    if not request.method == 'POST':
        return JsonError("error")

    d = JsonParse(request.POST.get('data'))

    if "location_in_task_times" in d:
        if d["location_in_task_times"] is True or d["location_in_task_times"] is False:
            set_user_value(request.user, "location_in_task_times", d["location_in_task_times"])

    if "language" in d:
        if d["language"] in [l[0] for l in settings.LANGUAGES]:
            set_user_value(request.user, "language", d["language"])
            set_language(request)

    if "date_format" in d:
        if d["date_format"] in [x for x in g.DATE_FORMATS]:
            set_user_value(request.user, "date_format", d["date_format"])

    if "first_day_of_week" in d:
        if d["first_day_of_week"] in ['monday', 'sunday']:
            set_user_value(request.user, "first_day_of_week", d["first_day_of_week"])

    d["email"] = request.user.email
    d["first_name"] = request.user.first_name
    d["pk"] = request.user.pk

    bluser = BlocklogicUser.objects.get(pk=request.user.pk)

    qdict = QueryDict('')
    qdict = qdict.copy()
    qdict.update(d)

    if "saving_user_profile" in d:
        user_form = BlocklogicUserChangeForm(qdict, instance=bluser)
        user_form.set_request(request)

        try:
            if user_form.is_valid():
                bluser.last_name = user_form.cleaned_data["last_name"]
                bluser.country = countries.country_by_code[user_form.cleaned_data["country"]]
                bluser.sex = user_form.cleaned_data["sex"]
                bluser.updated_by = bluser
                bluser.save()

        except Exception as e:
            return JsonError("error", _("There was error saving data. Contact support."))

        """
        user_profile_form = UserProfileForm(qdict, instance=bluser)

        try:
            if user_profile_form.is_valid():
                user_profile = UserProfile.objects.get(user=bluser)
                user_profile.company_name = user_profile_form.cleaned_data["company_name"]
                user_profile.company_address = user_profile_form.cleaned_data["company_address"]
                user_profile.company_postcode = user_profile_form.cleaned_data["company_postcode"]
                user_profile.company_city = user_profile_form.cleaned_data["company_city"]
                user_profile.company_website = user_profile_form.cleaned_data["company_website"]
                user_profile.company_country = user_profile_form.cleaned_data["company_country"]
                user_profile.company_tax_id = user_profile_form.cleaned_data["company_tax_id"]
                user_profile.company_tax_payer = user_profile_form.cleaned_data["company_tax_payer"]

                user_profile.updated_by = bluser
                user_profile.save()
        except Exception as e:
            return JsonError("error", _("There was error saving data. Contact support."))
        """

    return JsonOk()


@login_required
def update_password(request):
    if not request.method == 'POST':
        return JsonError("error")

    d = JsonParse(request.POST.get('data'))

    if 'current_password' not in d or 'password1' not in d or 'password2' not in d:
        return JsonError('error', _('Something went wrong during password saving. Contact support.'))

    if d['password1'] != d['password2']:
        return JsonError('new_password_mismatch', _('New passwords do not match'))

    if not min_password_requirments(d['password1']):
        return JsonError('min_pass_requirement_failed', _('Password minimal requirments failed.'))

    user = django_authenticate(username=request.user.email, password=d['current_password'])
    if user is None:
        return JsonError('wrong_current_password')

    if user is not None:
        user.set_password(d['password1'])
        user.save()

        return JsonOk()

    return JsonError('error', _('Something went wrong during password saving. Contact support.'))


@login_required
def user_profile(request, context):
    bluser = BlocklogicUser.objects.get(id=request.user.id)
    messages = {}
    update_password = False

    """
    try:
        user_profile = UserProfile.objects.get(user=bluser)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile(user=bluser, created_by=bluser)
        user_profile.save()
    """

    if request.method == 'POST':
        errors = {}

        # so we do not allow forging POST['email']
        POST = request.POST.copy()
        POST['email'] = request.user.email

        user_form = BlocklogicUserForm(POST)
        user_form.set_request(request)
        user_form.registration = False

        # user_profile_form = UserProfileForm(POST)

        if "update_password" in POST and POST.get('update_password', '') == "yes":
            update_password = True

        if user_form.is_valid():
            fd = user_form.cleaned_data

            bluser.first_name = fd.get('first_name', '')
            bluser.last_name = fd.get('last_name', '')
            bluser.country = fd.get('country', '')
            bluser.sex = fd.get('sex', '')

            if "update_password" in POST and POST.get('update_password', '') == "yes":
                password1 = fd.get('password1', '')
                password2 = fd.get('password2', '')

                if len(password1) > 0 and len(password2) > 0:
                    if password1 == password2:
                        bluser.set_password(password1)

            if 'images' in request.FILES and request.FILES['images'] and len(request.FILES['images']) > 0:
                # ne da se nam "bindat" samo eno sliko na "user profile", zato brisemo vse.
                # physically delete related image
                if POST.get('user_profile_image_id', "") != "":
                    delete_user_image(bluser, POST.get('user_profile_image_id', ""))

                user_image = UserImage(name=bluser.first_name + " " + bluser.last_name, original_filename=request.FILES['images'].name, created_by=bluser, updated_by=bluser)
                user_image.image.save(request.FILES['images'].name, ContentFile(request.FILES['images'].read()))
                user_image.save()

                bluser.images.add(user_image)

            bluser.save()

        """
        if user_profile_form.is_valid():
            fd = user_profile_form.cleaned_data

            user_profile.company_name = fd.get('company_name', '')
            user_profile.company_address = fd.get('company_address', '')
            user_profile.company_postcode = fd.get('company_postcode', '')
            user_profile.company_country = fd.get('company_country', '')
            user_profile.company_website = fd.get('company_website', '')
            user_profile.updated_by = request.user

            user_profile.save()

        if user_form.is_valid() and user_profile_form.is_valid():
            messages = {"success": _("Your data updated successfully!")}
        """

        if user_form.is_valid():
            messages = {"success": _("Your data updated successfully!")}

    else:
        initial = {'email': bluser.email, 'first_name': bluser.first_name, 'last_name': bluser.last_name,
                   'sex': bluser.sex, 'password1': bluser.password, 'password2': bluser.password, "country": bluser.country}

        user_form = BlocklogicUserForm(initial=initial)
        user_form.registration = False

        company_country = None
        if user_profile.company_country:
            company_country = user_profile.company_country

        initial_profile = {'company_name': user_profile.company_name,
                           'company_address': user_profile.company_address,
                           'company_postcode': user_profile.company_postcode,
                           'company_country': company_country,
                           'company_website': user_profile.company_website}
        # user_profile_form = UserProfileForm(initial=initial_profile)

    context['bluser'] = bluser
    # context['user_profile_form'] = user_profile_form
    context['countries'] = countries
    context['messages'] = messages
    context['update_password'] = update_password
    context['title'] = _("Settings")
    context['site_title'] = g.SITE_TITLE
    context['STATIC_URL'] = settings.STATIC_URL

    return context


@login_required
def remove_user_profile_image(request):
    if not request.is_ajax():
        raise Http404()

    bluser = BlocklogicUser.objects.get(id=request.user.id)

    d = JsonParse(request.POST.get('data'))

    if not 'image_id' in d or not d['image_id']:
        return JsonResponse({'status': 'error', 'message': _("Which photo to remove?")})

    if not delete_user_image(bluser, d['image_id']):
        return JsonResponse({'status': 'error', 'message': _("Could not delete image.")})

    return JsonResponse({'status': 'ok'})


@login_required
def save_last_used_group(request):
    if not request.is_ajax():
        raise Http404()

    bluser = BlocklogicUser.objects.get(id=request.user.id)

    d = JsonParse(request.POST.get('data'))

    if not 'group_id' in d or not d['group_id']:
        return JsonResponse({'status': 'error', 'message': _("Could not get group ID")})

    set_user_value(request.user, "last_used_group", d['group_id'])

    return JsonResponse({'status': 'ok'})


def get_user_credentials(user):
    credentials = {}
    return credentials

    group = user.homegroup

    credentials['group_name'] = group.name
    credentials['group_id'] = group.id
    #credentials['last_group_slug'] = GroupUserRole.objects.get(user=user, group=group).group_slug
    credentials['user_id'] = user.id
    credentials['user_email'] = user.email
    # credentials['other_groups'] = groups_to_dict(user.user_groups, user, participant=True)

    credentials['notifications'] = get_notifications(user)
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


def get_notifications(user):
    email = user.email
    actions = Action.objects.filter(_for=email, what="invitation", status=WAITING)

    data = []

    for a in actions:
        action_data = json.loads(a.data)
        """
        if "group_id" in action_data:
            g = Group.objects.get(id=action_data['group_id'])
            data.append(group_to_dict(g, user, True, a.reference))
        """

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
                    return JsonError(status="error", message="wrong credentials")

        elif backend == "google-oauth2":
            d = google_login_or_register(request, mobile=True)
            if d['status'] == 'ok':
                user = BlocklogicUser.objects.get(id=d['user_id'])
            else:
                return JsonResponse(d)

        else:
            return JsonError("error", "wrong login")

        token, created = Token.objects.get_or_create(user=user)

        if user:
            user_credentials = get_user_credentials(user)
        else:
            return JsonError("error", "this should not happen")
        company = Company.objects.get(id=1)
        return JsonResponse({'token': token.key,
                              'user': user_credentials,
                              'config': company_config_to_dict(request, company),
                              'status': "ok"})


def get_user(request):
    if request.user.is_authenticated():
        return request.user
    else:
        return None

@login_required
def user_settings(request):
    bluser = BlocklogicUser.objects.get(id=request.user.id)

    initial = {'email': bluser.email, 'first_name': bluser.first_name, 'last_name': bluser.last_name,
               'sex': bluser.sex, 'password1': bluser.password, 'password2': bluser.password}

    if bluser.country:
        initial["country"] = bluser.country.two_letter_code

    user_form = BlocklogicUserForm(initial=initial)
    user_form.registration = False

    company_country = None
    if user_profile.company_country:
        company_country = user_profile.company_country.two_letter_code

    # company_id
    context = base_context(request, "1")
    context["section"] = "settings"
    context["title"] = _("Settings")
    context['user_form'] = user_form
    context['languages'] = settings.LANGUAGES
    context['language'] = get_user_value(request.user, 'language')
    context['date_format'] = get_user_value(request.user, 'date_format')
    context['date_formats'] = [x for x in g.DATE_FORMATS]

    return render(request, "blusers/settings.html", context)

@login_required
def change_photo(request, android=False):
    if 'image' in request.FILES and request.FILES['image'] and len(request.FILES['image']) > 0:
        user = request.user

        for image in user.images.all():
            user_image = UserImage.objects.get(id=image.pk)
            user_image.delete()

        user.images.all().delete()

        #print request.FILES['image'].name
        #print request.FILES['image'].read()

        user_image = UserImage(name=user.first_name + " " + user.last_name, original_filename=request.FILES['image'].name, created_by=user, updated_by=user)
        user_image.image.save(request.FILES['image'].name, ContentFile(request.FILES['image'].read()))
        user_image.save()

        user.images.add(user_image)
        user.save()

        options = {'size': (150, 120), 'crop': True, 'quality': 100}
        user_image_photo_url = get_thumbnailer(user.images.all()[0].image).get_thumbnail(options).url

        options = {'size': (22, 22), 'crop': True, 'quality': 100}
        user_image_menu_url = get_thumbnailer(user.images.all()[0].image).get_thumbnail(options).url
        if android:
            return JsonResponse({"status": "ok", "user_image_photo_url": user_image_photo_url, "user_image_menu_url": user_image_menu_url})
        else:
            i = get_thumbnailer(user.images.all()[0].image)
            image = i.get_thumbnail({'size': (160, 160), 'crop': True})
            image.seek(0)
            image_read = image.read()
            encoded_string = base64.b64encode(image_read)

            return JsonResponse({"status": "ok", "image": encoded_string})

    return JsonResponse({"status": "no_image"})


obtain_auth_token = ObtainAuthToken.as_view()


