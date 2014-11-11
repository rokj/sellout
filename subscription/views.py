import copy
import datetime
import json
from dateutil.relativedelta import relativedelta
from django.db.models import Q

from django.shortcuts import render, redirect
from blusers.forms import UserProfileForm
from blusers.models import BlocklogicUser
from blusers.views import get_last_used_group
from common.globals import WAITING, PAID, CANCELED, RUNNING, ALMOST_PAID, FIRST_TIME, FREE, NOT_ENOUGH_MONEY_ARRIVED, \
    NO_MONEY_ARRIVED
from common.functions import site_title
from common.models import Currency
from common.views import base_context
from decorators import login_required
from django.utils.translation import ugettext as _
from payment.models import Payment
import settings
from subscription.models import Subscription, Subscriptions


@login_required
def subscriptions(request):
    group = get_last_used_group(request.user)

    context = base_context(request, group.id)

    try:
        subscription = Subscription.objects.get(user=request.user)
    except Subscription.DoesNotExist:
        Subscription.subscribe_for_the_first_time(request.user, request.user)

        subscription = Subscription.objects.get(user=request.user)

    waiting_payment_subscriptions = Payment.objects.filter(created_by=request.user, status=WAITING).order_by('datetime_created')

    subscriptions = Subscriptions.objects.filter(subscription=subscription).order_by("-datetime_created")

    my_payments = Payment.objects.filter(Q(status=PAID) | Q(status=NOT_ENOUGH_MONEY_ARRIVED) | Q(status=CANCELED), created_by=request.user).order_by('-datetime_created')

    previous = None

    for wps in waiting_payment_subscriptions:
        wps.other_users_included_in_payment = wps.other_users_included_in_payment(request.user)
        wps.me_included = wps.me_included_in_payment(request.user)

        if wps.me_included:
            if not previous:
                wps.start_date = subscription.expiration_date
                wps.end_date = wps.start_date + datetime.timedelta(days=wps.subscription_duration*31)
            else:
                wps.start_date = previous.end_date
                wps.end_date = wps.start_date + datetime.timedelta(days=wps.subscription_duration*31)

            previous = wps

    context["sepa_address"] = settings.PAYMENT["sepa"]
    context["subscription"] = subscription
    context["waiting_payment_subscriptions"] = waiting_payment_subscriptions
    context["subscriptions"] = subscriptions
    context["my_payments"] = my_payments
    context['show_hide_canceled_button'] = False
    context['user'] = request.user
    context['subscription'] = Subscription.objects.get(user=request.user)
    # 'others_included': None,
    # 'past_subscriptions': past_subscriptions,
    context['title'] = _("My subscriptions")
    context['site_title'] = site_title()
    context['section'] = 'settings'
    context['NOT_ENOUGH_MONEY_ARRIVED_STATUS'] = NOT_ENOUGH_MONEY_ARRIVED
    context['NO_MONEY_ARRIVED_STATUS'] = NO_MONEY_ARRIVED
    context['WAITING_STATUS'] = WAITING
    context['CANCELED_STATUS'] = CANCELED
    context['ALMOST_PAID_STATUS'] = ALMOST_PAID
    context['PAID_STATUS'] = PAID
    context['RUNNING_STATUS'] = RUNNING

    return render(request, 'subscription/subscriptions.html', context)


@login_required
def subscription(request):
    """
    When adding new subscription, this function is called.

    @param request:
    @return:
    """

    group = get_last_used_group(request.user)
    subscription = Subscription.objects.get(user=request.user)

    context = base_context(request, group.id)

    initial_profile = {'company_name': context["user_profile"].company_name,
                       'company_address': context["user_profile"].company_address,
                       'company_postcode': context["user_profile"].company_postcode,
                       'company_city': context["user_profile"].company_city,
                       'company_country': context["user_profile"].company_country,
                       'company_tax_id': context["user_profile"].company_tax_id,
                       'company_tax_payer': context["user_profile"].company_tax_payer
                       }

    user_profile_form = UserProfileForm(initial=initial_profile)
    context['user_profile_form'] = user_profile_form
    context['subscription'] = subscription
    context['from'] = subscription.expiration_date
    context['until'] = subscription.expiration_date + datetime.timedelta(days=31)
    context['sepa_transaction_fee'] = settings.PAYMENT['sepa']['transaction_fee']
    context['section'] = 'settings'
    context['subscription_price'] = settings.SUBSCRIPTION_PRICE
    context['title'] = _("Subscription payment")
    context['site_title'] = site_title()

    return render(request, 'subscription/subscription.html', context)
