# -*- coding: utf-8 -*-

import os
import string
import json
import random
from decimal import Decimal, ROUND_DOWN
import Image
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.defaultfilters import floatformat
from django.utils.deconstruct import deconstructible
import datetime as dtm
import time
import globals as g
import settings

def get_random_string(length=8, chars=string.letters + string.digits):
    return ''.join([random.choice(chars) for _ in xrange(length)])


def get_terminal_url(request):
# future store url: same as this page's, excluding what's after the
    # g.MISC['management_url'] string
    # blocklogic.net/pos/app/register-company >> blocklogic.net/pos/company-name
    full_url = request.build_absolute_uri()
    return full_url[:full_url.rfind(g.MISC['management_url'] + '/')]


def redirect_to_selected_company(user, ajax=False):
    from pos.models import Company

    selected_company = user.selected_company

    return redirect('pos:terminal', company=Company.objects.get(pk=int(selected_company).url_name))

    # if ajax:
        # return reverse('web:home', kwargs={'group_id': group.id, 'section': 'home'})

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

        # image extension (format)
        #ext = os.path.splitext(filename)[1] # for preserving the original format
        #ext = ext.lower()
        ext = '.' + g.MISC['image_format'].lower()  # to apply a fixed default

        random_filename = get_random_string(length=16)
        row = True
        while row:
            cursor.execute('SELECT id FROM ' + self.table_name + ' WHERE ' + self.field_name + ' = %s', [random_filename])
            if cursor.fetchone():
                row = True
                random_filename = get_random_string(length=8)
            else:
                row = False

        # instance.original_filename = filename
        return '%s/%s' % (self.path, random_filename + ext)

def redirect_to_subscriptions(ajax=False):
    if ajax:
        return reverse('subscription:new')

    return redirect('subscription:new')

def site_title():
    return g.SITE_TITLE

def send_email(sender, to=None, bcc=None, subject=None, txt=None, html=None, attachment=None):
    """
    This is commmon email send function.
    We always send in html and txt form.

    sender example: 'Rok Jaklič <rok@internet.com>'
    receiver: ['email-1@email.net', ['email-2@email.net', ...]
    """

    message = EmailMultiAlternatives(subject, txt, sender, to, bcc, headers={'Reply-To': sender})
    message.attach_alternative(html, "text/html")
    message.content_subtype = "html"
    message.send()

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

def JSON_ok(message=""):
    data = {'status': 'ok'}

    if message != "":
        data['message'] = message

    return JsonResponse(data)

def JSON_stringify(data):
    # the data will be put into template with |safe filter or
    # within {% autoescape off %},
    # so make sure there's no harmful stuff inside
    s = json.dumps(data)
    s = s.replace('<', '\u003c')
    s = s.replace('>', '\u003e')
    s = s.replace('&', '\u0026')

    return s

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

def JSON_parse(string_data):
    return json.loads(string_data)

def JSON_error(status="error", message=""):
    return JsonResponse({'status': status, 'message': message})

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