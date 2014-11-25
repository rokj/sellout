from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from blusers.forms import LoginForm
from common.functions import redirect_to_selected_company
from django.utils.translation import ugettext as _
from decorators import login_required
import settings


def index(request, login_form=None, message=None):
    """ a plain login/registration page without errors and data from form verification;
        if submitted data fails to verify, the view that verified it will
        re-use the same template with initialized forms """
    registration_successful = False
    action = ""

    if request.user.is_authenticated():
        return redirect('select_company')

    if request.POST.get('action', '') == 'login':
        from blusers.views import login

        message, next = login(request)

        action = 'login'

        if message == 'logged-in':
            return redirect('select_company')

    if not login_form:
        login_form = LoginForm()

    if message == 'logged-out':
        message = _("You have been logged out")
    if message == 'login-failed':
        message = _("Login failed, check username and password")
    elif message == 'user-inactive':
        message = _("Your username is inactive. Check email (maybe spam folder) again and activate account. If still does not work, just contact support")
    elif message == 'activation-successful':
        message = _("Activation successful, you can now login")
    elif message == 'activation-failed':
        message = _("Activation failed! (Wrong key?)")
    elif message == 'google-login':
        message = _("This email is used with Google login, so better try logging in with Google account, just by clicking on Google icon below")
    elif message == "no-selected-company":
        message = _("Something went wrong. Contact support.")

    next = None

    if request.GET.get('next', '') != '' and request.GET.get('next', '') != reverse('logout'):
        next = request.GET.get('next')

    context = {
        'action': action,
        'next': next,
        'message': message,
        'registration_successful': registration_successful,
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