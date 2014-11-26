from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from blusers.forms import LoginForm
from django.utils.translation import ugettext as _
from decorators import login_required
import settings


def index(request, login_form=None, message=None):
    if request.user.is_authenticated():
        return redirect('select_company')

    if request.method == 'POST':
        from blusers.views import login
        message, next = login(request)

        if message == 'logged-in':
            return redirect('select_company')

    if not login_form:
        login_form = LoginForm()

    next = None

    if request.GET.get('next') != '' and request.GET.get('next') != reverse('logout'):
        next = request.GET.get('next')

    context = {
        'next': next,
        'message': message,
        'login_form': login_form,
        'client_id': settings.GOOGLE_API['client_id'],
        'title': "",
        'site_title': settings.GLOBAL["site_title"],
        'STATIC_URL': settings.STATIC_URL,
        'GOOGLE_API': settings.GOOGLE_API
    }

    return render(request, "site/index.html", context)


@login_required
def select_company(request):
    message = ''

    user = request.user

    context = {
        'message': message,
        'user': user,
        'client_id': settings.GOOGLE_API['client_id'],
        'title': _("Select company"),
        'site_title': settings.GLOBAL["site_title"],
        'STATIC_URL': settings.STATIC_URL,
        'GOOGLE_API': settings.GOOGLE_API
    }

    return render(request, "site/select_company.html", context)