# -*- coding:utf-8 -*-
import json
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from action.models import Action
from common.functions import JsonParse, _get_subscription_price, get_subscription_btc_price
from config.functions import get_user_value

from decorators import login_required
import settings
from subscription.models import Subscription
import common.globals as g


@login_required
def get_subscription_price(request, duration, his_price=0):
    others = []

    d = JsonParse(request.POST.get('data'))

    if "others" in d:
        others = d['others'].split(",")

    if not "exclude_me" in d:
        others.append("including_me")

    payment_type = d["payment_type"]

    # removing duplicates
    others = list(set(others))

    price, transaction_fee = _get_subscription_price("EUR", int(duration), his_price, len(others), payment_type)

    # since the prices are the same in EUR and in USD, we do not need to set first parameter when calling
    # _get_subscription_btc_price
    data = {
        'status': 'ok',
        'price': str(price),
        'transaction_fee': str(transaction_fee)
    }

    if payment_type == "bitcoin":
        data['btc_price'] = str(get_subscription_btc_price("from_eur", int(duration), his_price, len(others)))

    return JsonResponse(data)

def base_context(request, company_id):
    Subscription.is_subscription_almost_over(request.user)
    Subscription.is_subscription_over(request.user)

    actions = Action.objects.filter(status=g.WAITING, _for=request.user.email)

    for a in actions:
        if a.what == "invitation":
            a.data = json.loads(a.data)
            #if get_language() == "sl-si":
            #    accept_url = "sprejmi-povabilo-v-skupino/kljuc=%s" % (a.reference)
            #    decline_url = "zavrni-povabilo-v-skupino/kljuc=%s" % (a.reference)

            #    a.accept_url = settings.SITE_URL + settings.URL_PREFIX + accept_url
            #    a.decline_url = settings.SITE_URL + settings.URL_PREFIX + decline_url
            #else:

            accept_url = "accept-group-invitation/key=%s" % (a.reference)
            decline_url = "decline-group-invitation/key=%s" % (a.reference)

            a.accept_url = settings.SITE_URL + settings.URL_PREFIX + accept_url
            a.decline_url = settings.SITE_URL + settings.URL_PREFIX + decline_url


    # user_groups = request.user.get_user_groups()

    """
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    """""

    context = {
        'bluser': request.user,
        # 'user_profile': user_profile,
        'GOOGLE_API': settings.GOOGLE_API,
        'actions': actions,
        'subscription_link': reverse('subscription:new'),
        # json values

        # settings, config
        'title': "",  # will be overwritten by javascript
        'language': get_user_value(request.user, "language"),
        'clock_range': get_user_value(request.user, "clock_range"),
        'site_title': g.SITE_TITLE,
        'group_notes_keepalive': g.GROUP_NOTES_KEEPALIVE,
        'date_format': g.DATE_FORMATS[get_user_value(request.user, 'date_format')]['jquery'] if request.user.is_authenticated() else g.DATE_FORMATS[g.DEFAULT_DATE_FORMAT]['jquery'],

        'field_lengths': {
            'max_notes_size': g.MAX_NOTES_SIZE,
        }
    }

    return context