import json
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from action.models import Action
from blusers.forms import LoginForm
from django.utils.translation import ugettext as _
from decorators import login_required

import common.globals as g
import settings


def index(request):
    if request.user.is_authenticated():
        return redirect('select_company')

    message = None

    if request.method == 'POST':
        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            from blusers.views import login
            message, next = login(request, login_form.cleaned_data)

            if message == 'logged-in':
                return redirect('select_company')
    else:
        login_form = LoginForm()

    next = None

    if request.GET.get('next') != '' and request.GET.get('next') != reverse('logout'):
        next = request.GET.get('next')

    context = {
        'next': next,
        'login_message': message,
        'login_form': login_form,
        'client_id': settings.GOOGLE_API['client_id'],
        'title': "",
        'site_title': g.SITE_TITLE,
        'STATIC_URL': settings.STATIC_URL,
        'GOOGLE_API': settings.GOOGLE_API
    }

    return render(request, "site/index.html", context)


@login_required
def select_company(request):
    """ show current user's companies and a list of invites. """

    # the list of companies
    companies = request.user.get_companies()

    # the list of messages
    actions = Action.objects.filter(status="waiting", _for=request.user.email)

    for a in actions:
        if a.what == "invitation":
            a.data = json.loads(a.data)

            # if get_language() == "sl-si":
            #    accept_url = "sprejmi-povabilo-v-skupino/kljuc=%s" % (a.reference)
            #    decline_url = "zavrni-povabilo-v-skupino/kljuc=%s" % (a.reference)

            #    a.accept_url = settings.SITE_URL + settings.URL_PREFIX + accept_url
            #    a.decline_url = settings.SITE_URL + settings.URL_PREFIX + decline_url
            #else:

            # TODO: use reverse()
            accept_url = "accept-group-invitation/key=%s" % (a.reference)
            decline_url = "decline-group-invitation/key=%s" % (a.reference)

            a.accept_url = settings.SITE_URL + accept_url
            a.decline_url = settings.SITE_URL + decline_url

    context = {
        'title': _("Select company"),
        'site_title': g.SITE_TITLE,

        'companies': companies,
        'actions': actions
    }

    return render(request, "site/select_company.html", context)