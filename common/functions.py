# -*- coding: utf-8 -*-
import os
import string
import json
import random
from decimal import Decimal, ROUND_DOWN
from django import forms

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import connection, IntegrityError, connections
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext as _

import datetime as dtm
import time
import globals as g
import settings


def get_random_string(length=8, chars=string.letters + string.digits):
    return ''.join([random.choice(chars) for _ in xrange(length)])


# requests and responses
def error(request, company, message):

    context = {
        'company': company,
        'message': message,
        'title': _("Error"),
        'site_title': g.MISC['site_title'],
        'back_link': request.build_absolute_uri(),
    }

    return render(request, 'pos/error.html', context)


def JsonStringify(data):
    # the data will be put into template with |safe filter or
    # within {% autoescape off %},
    # so make sure there's no harmful stuff inside
    s = json.dumps(data)
    s = s.replace('<', '\u003c')
    s = s.replace('>', '\u003e')
    s = s.replace('&', '\u0026')

    return s


def JsonError(message, extra=None):
    d = {
        'status': 'error',
        'message': message
    }

    if extra:
        d['extra'] = extra

    return JsonResponse(d)


def JsonOk(extra=None, safe=True):

    data = {'status': 'ok'}
    if extra is not None:  # if extra is empty list or dict, it still has to be included
        data['data'] = extra

    return JsonResponse(data, safe=safe)


def JsonParse(string_data):
    try:
        return json.loads(string_data)
    except:
        return None


# misc
def max_field_length(model, field_name):
    l = model._meta.get_field(field_name).max_length

    if l:
        return l
    else:
        return None


# numbers
def format_number(user, company, n, high_precision=False):
    """ returns formatted decimal number n;
        strips zeros, but leaves <p> numbers after decimal point even if they are zero
    """
    from config.functions import get_company_value
    sep = get_company_value(user, company, 'pos_decimal_separator')
    p = int(get_company_value(user, company, 'pos_decimal_places'))

    if not n:
        return '0'

    if high_precision:
        s = str(n.quantize(Decimal('1.'+'0'*2*p)))
    else:
        s = str(n.quantize(Decimal('1.' + '0' * p)))

    return s.replace('.', sep)


def format_date(user, company, date, send_to='python'):
    """ formats date for display according to user's settings """

    from config.functions import get_date_format

    if not date:
        return ''
    else:
        return date.strftime(get_date_format(user, company, send_to))


def format_time(user, company, date):
    """ formats time for display according to user's settings """

    from config.functions import get_time_format

    if not date:
        return ''
    else:
        return date.strftime(get_time_format(user, company, 'python'))


def parse_decimal(user, company, string, max_digits=None):
    """ replace user's decimal separator with dot and parse
        return dictionary with result status and parsed number:

        {'success':True/False, number:<num>/None}
    """

    from config.functions import get_company_value

    if user:  # if user is None, try with the dot (user should never be None -
              # this is to avoid checking on every function call)
        string = string.replace(get_company_value(user, company, 'pos_decimal_separator'), '.')

    # check for entries too big
    if max_digits:
        if string.find('.') == -1:  # it's an integer, it has no 'decimal point'
            if len(string) > max_digits:
                return {'success': False, 'number': None}
        if string.find('.') > max_digits:  # it's a float, the integer part shouldn't be longer than max_digits
            return {'success': False, 'number': None}

    try:
        number = Decimal(string)
        return {'success': True, 'number': number}
    except:
        return {'success': False, 'number': None}


def parse_decimal_exc(user, company, string, max_digits=None, message=_("Invalid number format")):
    r = parse_decimal(user, company, string, max_digits)
    if not r['success']:
        raise ValueError(message)
    else:
        return r['number']


def parse_date(user, company, string):
    """ parses date in string according to user selected preferences
        return dictionary with result status and parsed datetime:

        {'success':True/False, date:<num>/None}
    """

    from config.functions import get_date_format

    try:
        d = dtm.datetime.strptime(string, get_date_format(user, company, 'python'))
    except:
        return {'success': False, 'date': None}

    return {'success': True, 'date': d}


# permissions: cached
def permission_cache_key(user, company):
        return "permission_" + str(user.id) + "_" + str(company.id)


def has_permission(user, company, model, task):
    """ returns True if the user has the required permissions
        for the given company, model and task

        model is a string

        task can be: 'view' or 'edit' (edit includes add, edit, delete)
    """

    # get permission from memcache...

    from pos.models import Permission

    ckey = permission_cache_key(user, company)
    permission = cache.get(ckey)
    # ...or database
    if not permission:
        try:
            permission = Permission.objects.get(user=user, company=company)
            cache.set(ckey, permission)
        except Permission.DoesNotExist:
            # there's no entry in the database,
            # therefore the user has no permissions whatsoever
            return False

    if model in g.PERMISSIONS[permission.permission][task]:
        return True
    else:
        return False


def no_permission_view(request, company, action):
    """ the view that is called if user attempts to do shady business without permission """

    context = {
        'title': _("Permission denied"),
        'site_title': g.MISC['site_title'],
        'company': company,  # required for the 'manage' template: links need company parameter
        'action': action,
    }

    return render(request, 'pos/no_permission.html', context)


### deletion of objects in management
def manage_delete_object(request, company_url_name, model, messages):
    """
        a generic delete function (must be wrapped in a view)
        model: the actual model class (i.e. Discount)
        messages: a list of error messages:
           messages[0]: no permission
           message[1]: does not exist/integrity error
    """
    from pos.models import Company

    try:
        c = Company.objects.get(url_name=company_url_name)
        return manage_delete_object_(request, c, model, messages)
    except Company.DoesNotExist:
        return JsonError(_("Company not found"))


def manage_delete_object_(request, c, model, messages):
    # check permissions
    if not has_permission(request.user, c, model.__name__.lower(), 'edit'):
        return JsonError(messages[0])

    # object id is in request.POST in JSON format
    id = JsonParse(request.POST.get('data')).get('id')
    if not id:
        return JsonError(_("No id specified."))

    try:
        model.objects.get(id=id, company=c).delete()
    except (model.DoesNotExist, IntegrityError) as e:
        return JsonError(messages[1] + "; " + e.message)

    return JsonOk()


###
### stuff for working on similar models
###
# (like Contact - BillContact: almost all fields on both models are inherited from ContactAbstract)
def get_common_keys(dict1, dict2):
    """ returns a list common keys in two dictionaries """
    return list(set(dict1.keys()) & set(dict2.keys()))


def remove_skeleton_fields(fields):
    """
        exclude names of all fields from SkeletonU: created_by, updated_by, timestamps etc...
        but no hardcoding, Mr. Beaufort!
    """

    from common.models import SkeletonU

    skeleton_fields = SkeletonU._meta.get_all_field_names() + ['id']  # id must be assigned by database

    for field in skeleton_fields:
        if field in fields:
            fields.remove(field)

    return fields


def compare_objects(obj1, obj2):
    """
        comparation of two different models with the same data
        (used for checking if Company has changed so that it needs a new BillCompany entry)
        (applies to other models as well - BillContact, BillRegister)
    """
    d1 = model_to_dict(obj1)
    d2 = model_to_dict(obj2)

    common_fields = remove_skeleton_fields(get_common_keys(d1, d2))

    # if any of the fields mismatch, the models are not equal.
    for key in common_fields:
        if d1[key] != d2[key]:
            return False

    # the models are equal.
    return True


def copy_data(from_obj, to_obj):
    """
        copy data from fields in obj1 to fields in obj2.
        only do this for fields that are on both objects;
        those are fields from the same abstract
    """
    from_d = from_obj.__dict__
    to_d = to_obj.__dict__

    common_fields = remove_skeleton_fields(get_common_keys(from_d, to_d))

    # copy all common fields' values from obj1 to obj2
    for field in common_fields:
        to_d[field] = from_d[field]


# custom forms and fields...
class CompanyUserForm(forms.Form):
    def __init__(self, user=None, company=None, *args, **kwargs):
        super(CompanyUserForm, self).__init__(*args, **kwargs)

        assert user
        assert company

        self.user = user
        self.company = company

        # set user and company to all fields in this form
        for f in getattr(self, 'fields', None):
            self.fields[f].user = self.user
            self.fields[f].company = self.company


class CustomDateField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(CustomDateField, self).__init__(*args, **kwargs)

        # these will be set by CompanyUserForm;
        self.user = None
        self.company = None

    def clean(self, date):
        if not date:
            return None

        assert self.user is not None
        assert self.company is not None

        r = parse_date(self.user, self.company, date)
        if not r['success']:
            raise ValidationError(_("Invalid date format"), None)
        else:
            return r['date']


class CustomDecimalField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(CustomDecimalField, self).__init__(*args, **kwargs)

        # these will be set by CompanyUserForm;
        self.user = None
        self.company = None

    def clean(self, number):
        if not number:
            return None

        assert self.user is not None
        assert self.company is not None

        r = parse_decimal(self.user, self.company, number)
        if not r['success']:
            raise ValidationError(_("Invalid number format"), None)
        else:
            return r['number']


def get_terminal_url(request):
    # future store url: same as this page's, excluding what's after the
    # g.MISC['management_url'] string
    # blocklogic.net/pos/app/register-company >> blocklogic.net/pos/company-name
    full_url = request.build_absolute_uri()
    return full_url[:full_url.rfind(g.MISC['management_url'] + '/')]


@deconstructible
class ImagePath(object):
    """ returns a random name for a newly uploaded image;
        takes care of the birthday problem """
    def __init__(self, path, table_name, field_name="image"):
        self.path = path
        self.table_name = table_name
        self.field_name = field_name

    def __call__(self, instance, filename):
        if not filename or len(filename) == 0:
            filename = getattr(instance, self.field_name)
        cursor = connection.cursor()

        FILENAME_LENGTH = 16

        # image extension (format)
        #ext = os.path.splitext(filename)[1] # for preserving the original format
        #ext = ext.lower()
        ext = '.' + g.MISC['image_format'].lower()  # to apply a fixed default

        random_filename = get_random_string(length=FILENAME_LENGTH)
        row = True
        while row:
            cursor.execute('SELECT id FROM ' + self.table_name + ' WHERE ' + self.field_name + ' = %s', [random_filename])
            if cursor.fetchone():
                row = True
                random_filename = get_random_string(length=FILENAME_LENGTH)
            else:
                row = False

        # instance.original_filename = filename
        return '%s/%s' % (self.path, random_filename + ext)


def send_email(sender, to=None, bcc=None, subject=None, txt=None, html=None, attachment=None):
    """
    This is commmon email send function.
    We always send in html and txt form.

    sender example: 'Rok Jaklič <rok@internet.com>'
    receiver: ['email-1@email.net', ['email-2@email.net', ...]
    """
    try:
        """
        txt = txt.decode("utf-8")
        html = html.decode("utf-8")
        subject = subject.decode("utf-8")
        """
        message = EmailMultiAlternatives(subject, txt, sender, to, bcc, headers={'Reply-To': sender})
        message.attach_alternative(html, "text/html")
        message.content_subtype = "html"
        message.send()
    except Exception as e:
        print e


"""
def get_subscription_btc_price(from_what="from_eur", for_duration=1, his_price=0, nr_people=1):
    btc_price = -1

    if nr_people == 0:
        return 0

    try:
        f = open(settings.BTC_PRICE, "r")

        last_modified = dtm.datetime.utcfromtimestamp(os.path.getmtime(settings.BTC_PRICE))
        now = dtm.datetime.utcfromtimestamp(time.time())

        diff = now-last_modified
        diff_minutes = diff.seconds/60

        if diff_minutes > settings.MAX_BTC_PRICE_UPDATE_INTERVAL:
            btc_price = -1

            subject = "Probably could not update BTC price (check %s)." % (settings.BTC_PRICE)
            message_txt = "Look subject!"
            message_html = message_txt

            if settings.DEBUG:
                print subject
            else:
                send_email(settings.EMAIL_FROM, [settings.EMAIL_FROM], None, subject, message_txt, message_html)
        else:
            for line in f.readlines():
                price = line.strip().split(": ")

                if from_what == "from_eur":
                    if price[0] == settings.EXCHANGE_BTCEUR:
                        btc_price = price[1]

        if btc_price == -1:
            return btc_price

        if his_price > 0:
            btc_price = Decimal(btc_price)*Decimal(his_price)

        if for_duration > 1:
            btc_price = Decimal(btc_price)*Decimal(for_duration)

        btc_price = Decimal(btc_price)*Decimal(nr_people)

        return Decimal(btc_price).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)

    except IOError:
        subject = "Could not get BTC price for subscription payment (check %s that it exists)." % (settings.BTC_PRICE)
        message_txt = "Look subject!"
        message_html = message_txt

        if settings.DEBUG:
            print subject
        else:
            send_email(settings.EMAIL_FROM, [settings.EMAIL_FROM], None, subject, message_txt, message_html)

    return btc_price


def _get_subscription_price(in_what="EUR", duration=1, his_price=0, nr_people=1, payment_type="sepa"):
    real_duration = 1

    if duration == 2:
        real_duration = 2
    elif duration == 3:
        real_duration = 3
    elif duration == 5:
        real_duration = 6
    elif duration == 10:
        real_duration = 12

    if in_what not in settings.SUBSCRIPTION_PRICE:
        return -1

    if str(real_duration) + "_months" not in settings.SUBSCRIPTION_PRICE[in_what]:
        return -1

    price = settings.SUBSCRIPTION_PRICE[in_what][str(real_duration) + "_months"]*nr_people

    transaction_fee = 0

    if payment_type == "sepa":
        transaction_fee = settings.PAYMENT["sepa"]["transaction_fee"]
        price = price + transaction_fee
    elif payment_type == "paypal":
        # paypal price is calculated according
        # https://www.paypal.com/si/cgi-bin/webscr?cmd=_display-fees-outside
        transaction_fee = (price * 0.034) + 0.35
        price = price + transaction_fee

    return floatformat(price, 2), floatformat(transaction_fee, 2)
"""

min_pass_length = 6
pass_allowed_chars = set(string.letters + string.digits + '@#$%^&+=')
def min_password_requirments(password):
    if (len(password) < min_pass_length):
        # raise ValidationError(_("Password is too short.", code='password_to_short'))
        return False
    if any(pass_char not in pass_allowed_chars for pass_char in password):
        # raise ValidationError(_("Password contains illegal characters.", code='illegal_characters'))
        return False

    return True


def calculate_btc_price(currency="EUR", price=0):
    btc_price = -1

    cursor = connections['bitcoin'].cursor()

    exchange = settings.PAYMENT_OFFICER["btc_exchange"][currency]
    key = exchange + "_1_" + currency.lower() + "btc"

    try:
        cursor.execute("SELECT value, datetime_updated FROM bitcoin WHERE key = %s", (key,))
    except Exception as e:
        return btc_price

    rows = cursor.fetchall()

    if len(rows) == 0:
        return btc_price

    last_modified = rows[0][1]
    now = dtm.datetime.utcnow()

    diff = now-last_modified
    diff_minutes = diff.seconds/60

    if diff_minutes > settings.MAX_BTC_PRICE_UPDATE_INTERVAL:
        btc_price = -1

        subject = "BTC price was not updated for some time (check %s)." % (str(settings.MAX_BTC_PRICE_UPDATE_INTERVAL))
        message_txt = "Look subject!"
        message_html = message_txt

        if settings.DEBUG:
            print subject
        else:
            send_email(settings.EMAIL_FROM, [settings.EMAIL_FROM], None, subject, message_txt, message_html)

        return btc_price

    btc_price = Decimal(rows[0][0])*Decimal(price)

    return Decimal(btc_price).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)

def JSON_parse(string_data):
    return json.loads(string_data)