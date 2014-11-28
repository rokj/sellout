# -*- coding:utf-8 -*-
import datetime
from django.template.defaultfilters import floatformat
import json
import string

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template_from_string
from django.utils.translation import ugettext as _
from django.template import Context, Template
from django.template import defaultfilters
import re

from blusers.models import BlocklogicUser
from common.globals import WAITING, PAID, CANCELED, APPROVED
from common.functions import JSON_ok, JSON_parse, JSON_error, get_subscription_btc_price, send_email, \
    _get_subscription_price, get_random_string, get_bitcoin_user
from common.models import Currency
from decorators import login_required
from payment.service.Bitcoin import BitcoinRPC
from payment.models import Payment
from payment.service.Paypal import Paypal
import settings
from subscription.models import Subscription, Subscriptions


def paypal_return_url(request, transaction_reference):
    try:
        payment = Payment.objects.get(transaction_reference=transaction_reference)
        payment.status = APPROVED
        payment.save()
    except Payment.DoesNotExist:
        # TODO:
        HttpResponse(_("Payment with this reference does not exist."))

    approve_url = None
    if payment.payment_info and payment.payment_info != "":
        payment_info = json.loads(payment.payment_info)

        if payment_info and "links" in payment_info:
            for link in payment_info["links"]:
                if link["rel"] == "execute":
                    approve_url = link["href"]
                    break

    payer_id = request.GET.get('PayerID')

    paypal = Paypal()
    if not payer_id or not approve_url or not paypal.execute_payment(approve_url, payer_id):
        return JSON_error("error", _("Something went wrong during paypal payment. Please try again later or be nice "
                                     "and contact support."))

    payment.transaction_datetime = datetime.datetime.now()
    payment.status = PAID
    payment.save()

    Subscription.extend_subscriptions(payment)

    payment.send_payment_confirmation_email()

    return redirect('subscription:subscriptions')


def paypal_cancel_url(request, transaction_reference):
    try:
        payment = Payment.objects.get(transaction_reference=transaction_reference)
        payment.status = CANCELED
        payment.save()
    except Payment.DoesNotExist:
        HttpResponse('something_bad_happend')

    return redirect('subscription:subscriptions')


def pay_for_everyone(request, real_duration, users, payment_type):
    new_subscriptions = []

    for u in users:
        try:
            user = BlocklogicUser.objects.get(email=u)
            Subscription.subscribe_for_the_first_time(user, request.user)
            subscription = Subscription.objects.get(user=user)
        except BlocklogicUser.DoesNotExist:
            Subscription.subscribe_for_the_first_time(u, request.user)
            subscription = Subscription.objects.get(email=u)

        new_subscriptions.append(subscription)

    return new_subscriptions


def actual_payment(request, payment_type, mobile=False):
    from mobile.views import payment_to_dict
    data = {}
    d = JSON_parse(request.POST.get('data'))

    if "duration" not in d:
        return JSON_error("error", _("Error occured during payment. Please try again later or be nice and contact support."))

    users = [request.user.email]

    if "others" in d:
        others = d['others'].split(",")
        others = list(set(others))

        for o in others:
            try:
                validate_email(o)
                users.append(o)
            except ValidationError:
                continue

    if "exclude_me" in d:
        users.remove(request.user.email)

    duration = d['duration']
    real_duration = 1

    if duration == "1":
        duration = 1
    elif duration == "2":
        duration = 2
        real_duration = 2
    elif duration == "3":
        duration = 3
        real_duration = 3
    elif duration == "6":
        duration = 5
        real_duration = 6
    elif duration == "12":
        duration = 10
        real_duration = 12
    else:
        duration = 1

    price, transaction_fee = _get_subscription_price("EUR", duration, 0, len(users), payment_type)

    if payment_type == "bitcoin":
        btc_price = str(d['btc_price'])
        real_btc_price = str(get_subscription_btc_price("from_eur", duration, 0, len(users)))

        if btc_price != real_btc_price:
            return JsonResponse({"status": "btc_price_changed", 'message': _("BTC price changed during your stay on this page. New price is %s. "
                                                     "Is this still ok?" % real_btc_price), 'btc_price': real_btc_price})

        try:
            bitcoin_rpc = BitcoinRPC(settings.PAYMENT['bitcoin']['host'], settings.PAYMENT['bitcoin']['port'],
                                     settings.PAYMENT['bitcoin']['rpcuser'], settings.PAYMENT['bitcoin']['rpcpassword'])
            address = bitcoin_rpc.get_new_address(get_bitcoin_user(request.user.email))
        except Exception as e:
            subject = "ERROR when getting BTC address for user"
            message = "... for user %s" % (request.user.email)
            if (settings.DEBUG):
                print subject
                print message

                print e
            else:
                send_email(settings.EMAIL_FROM, [settings.EMAIL_FROM], None, "ERROR when getting BTC address for user",
                           message, message)

            return JSON_error("error", _("Error occured during payment. Please try again later or be nice and contact support."))

    new_subscriptions = []

    for s in pay_for_everyone(request, real_duration, users, payment_type):
        new_subscriptions.append(s)

    payment = Payment(type=payment_type, status=WAITING, currency=Currency.objects.get(code="EUR"), total=price, created_by=request.user)

    if payment_type == "bitcoin":
        payment.currency = Currency.objects.get(code="BTC")
        payment.transaction_reference = address
        payment.total_btc = real_btc_price
    elif payment_type == "sepa" or payment_type == "paypal":
        if payment_type == "sepa":
            transaction_reference = get_random_string(10, string.digits)

            # total price for SEPA is price + SEPA transaction fee
            price += floatformat(settings.PAYMENT['sepa']['transaction_fee'], arg=2)

        elif payment_type == "paypal":
            transaction_reference = get_random_string(20)
        while 1:
            try:
                payment = Payment.objects.get(transaction_reference=transaction_reference)
            except Payment.DoesNotExist:
                break

        payment.transaction_reference = transaction_reference

    payment.save()

    for ns in new_subscriptions:
        payment.save()
        payment.subscription.add(ns)

    if payment_type == "paypal":
        return_url = reverse('payment:paypal_return_url', kwargs={'transaction_reference': payment.transaction_reference})
        return_url = settings.PAYMENT['paypal']['host_for_return_url'] + return_url

        cancel_url = reverse('payment:paypal_cancel_url', kwargs={'transaction_reference': payment.transaction_reference})
        cancel_url = settings.PAYMENT['paypal']['host_for_cancel_url'] + cancel_url

        paypal = Paypal()
        if not paypal.pay(price, "EUR", real_duration, return_url, cancel_url):
            return JSON_error("error", _("Something went wrong during paypal payment. Please try again later or be nice and contact support."))

        if paypal.response and "links" in paypal.response:
            for link in paypal.response["links"]:
                if link["rel"] == "approval_url":
                    data["redirect_url"] = link["href"]
                    break

        payment.payment_info = json.dumps(paypal.response)
        payment.save()

    if payment.payment_info is not None:
        payment_info = json.loads(payment.payment_info)
    else:
        payment_info = {}

    try:
        just_others = users.remove(request.user.email)
    except ValueError:
        just_others = users

    if just_others is not None and len(just_others) > 0:
        just_others = ",".join(just_others)
    else:
        just_others = ""

    payment_info["others_included"] = just_others
    payment_info["subscription_duration"] = real_duration
    payment_info["transaction_fee"] = transaction_fee

    if "company_name" in d:
        payment_info["company_name"] = d["company_name"]

        if "company_address" in d:
            payment_info["company_address"] = d["company_address"]
        if "company_postname" in d:
            payment_info["company_city"] = d["company_city"]
        if "company_postcode" in d:
            payment_info["company_postcode"] = d["company_postcode"]
        if "company_country" in d:
            payment_info["company_country"] = d["company_country"]
        if "company_tax_id" in d:
            payment_info["company_tax_id"] = d["company_tax_id"]
        if "company_tax_payer" in d:
            payment_info["company_tax_payer"] = d["company_tax_payer"]

    payment.payment_info = json.dumps(payment_info)
    payment.save()

    data["others_included"] = ",".join(payment.other_users_included_in_payment(request.user))

    data["status"] = "ok"
    data["price"] = price

    if payment_type == "bitcoin":
        data["btc_price"] = real_btc_price
        data["btc_address"] = address
    elif payment_type == "sepa":
        data["sepa_company_name"] = settings.PAYMENT["sepa"]["company"]
        data["sepa_company_address"] = settings.PAYMENT["sepa"]["company_address"]
        data["sepa_company_postal_code"] = settings.PAYMENT["sepa"]["company_postal_code"]
        data["sepa_company_city"] = settings.PAYMENT["sepa"]["company_city"]
        data["sepa_company_country"] = settings.PAYMENT["sepa"]["company_country"]
        data["sepa_company_iban"] = settings.PAYMENT["sepa"]["iban"]
        data["sepa_transaction_reference"] = transaction_reference
    if mobile:
        data = {
            'status': "ok",
            'extra': payment_to_dict(payment)
        }
        return JsonResponse(data)

    else:
        return JsonResponse(data)

@login_required
def invoice(request, payment):
    invoice_html = ""
    try:
        p = Payment.objects.get(id=payment, created_by=request.user)
        invoice_html = p._parse_message_html()
    except Payment.DoesNotExist:
        pass

    for match in re.findall('<div id="message">(.*?)</div>', invoice_html, re.S):
        invoice_html = invoice_html.replace(match, "")
    for match in re.findall('<div id="message_wrapper">(.*?)</div>', invoice_html, re.S):
        invoice_html = invoice_html.replace(match, "")

    invoice_html = invoice_html.replace("<hr>", "")

    return HttpResponse(invoice_html)

@login_required(ajax=True)
def pay(request, mobile=False):
    d = JSON_parse(request.POST.get('data'))
    payment_type = d['type']

    if payment_type == "bitcoin" or payment_type == "sepa" or payment_type == "paypal":
        return actual_payment(request, payment_type, mobile)

    return JSON_error("no_such_currency", _("No such currency..."))


@login_required(ajax=True)
def cancel_payment(request, payment):
    try:
        payment = Payment.objects.get(id=payment, created_by=request.user)
        for s in payment.subscription.all():
            s.status = CANCELED
            s.save()

        payment.status = CANCELED
        payment.save()
    except Payment.DoesNotExist:
        return JSON_error("no_payment")

    return JSON_ok()

@login_required
def payment_info(request, payment):
    messages = {}

    try:
        payment = Payment.objects.get(id=payment, created_by=request.user)
    except Payment.DoesNotExist:
        messages["error"] = _("No such payment or something.")

    context = {
        'payment': payment,
        'messages': messages,
        'title': _("Payment for subscription/s"),
        'site_title': g.SITE_TITLE,
        'WAITING_STATUS': WAITING,
        'CANCELED_STATUS': CANCELED,
    }

    return render(request, 'payment/payment_info.html', context)

