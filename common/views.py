# -*- coding:utf-8 -*-
import django
from django.core.urlresolvers import reverse
from django.utils.translation import get_language
from jsonrpc import json
from action.models import Action
from blusers.models import UserProfile
from common.functions import get_subscription_btc_price as _get_subscription_btc_price, JsonResponse, JSON_parse, \
    _get_subscription_price, JSON_stringify, site_title, max_field_length
from common.globals import WAITING, PRIORITIES, TASK_COLORS, TASK_TYPES, MONTHS, DAYS
from config.functions import get_value
from decorators import login_required
from group.models import Group
import settings
from subscription.models import Subscription
from tasks.models import Task, Time
from tasks.views.cal import get_ongoing_time
from tasks.views.data import group_members, autocomplete_task_list
import common.globals as g


@login_required(ajax=True)
def get_subscription_price(request, duration, his_price=0):
    others = []

    d = JSON_parse(request.POST.get('data'))

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
        data['btc_price'] = str(_get_subscription_btc_price("from_eur", int(duration), his_price, len(others)))

    return JsonResponse(data)


def base_context(request, group_id):
    Subscription.is_subscription_almost_over(request.user)
    Subscription.is_subscription_over(request.user)

    group = Group.objects.get(id=group_id)
    actions = Action.objects.filter(status=WAITING, _for=request.user.email)

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

    gm = group_members(group)

    user_groups = request.user.get_user_groups()

    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    context = {
        'bluser': request.user,
        'user_profile': user_profile,
        'GOOGLE_API': settings.GOOGLE_API,
        'actions': actions,
        'ongoing_time': JSON_stringify(get_ongoing_time(request.user, group)),
        'group': group,  # current group
        'groups': user_groups,  # all groups the user is in
        'is_admin': group.has_admin(request.user),
        'group_members': gm,  # for use in templates
        'months': MONTHS,
        'subscription_link': reverse('subscription:new'),
        # json values
        'group_members_json': JSON_stringify(gm),  # for use with javascript (directly with {% autoescape off %}

        # settings, config
        'title': "",  # will be overwritten by javascript
        'language': get_value(request.user, "language"),
        'site_title': site_title(),
        'date_format': g.DATE_FORMATS[get_value(request.user, 'date_format')]['jquery'] if request.user.is_authenticated() else g.DATE_FORMATS[g.DEFAULT_DATE_FORMAT]['jquery'],
    }

    return context
