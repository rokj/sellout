from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from common.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required as login_required_nolocking
from django.core.context_processors import csrf

from django.contrib.auth import logout as django_logout, authenticate
from django.contrib.auth import login as django_login
from config import currencies
from pos.models import Company, Permission
from pos.views.manage.category import get_all_categories_structured
from pos.views.manage.company import company_to_dict
from pos.views.manage.contact import get_all_contacts
from pos.views.manage.discount import get_all_discounts
from pos.views.manage.product import get_all_products
from pos.views.manage.tax import get_all_taxes
from pos.views.manage.register import get_all_registers

from common.functions import has_permission, no_permission_view, JsonOk, JsonParse, JsonStringify, error, JsonError
from config.functions import get_user_value, set_user_value, get_date_format, get_time_format, get_company_value
from config.countries import country_choices
import common.globals as g


### index
@login_required
def terminal(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # see if user has permissions to use/see this terminal
    if not has_permission(request.user, c, 'terminal', 'view'):
        return no_permission_view(request, c, _("You have no permission to use terminal."))

    config = {
        # user's data
        'currency': get_company_value(request.user, c, 'pos_currency'),
        'separator': get_company_value(request.user, c, 'pos_decimal_separator'),
        'decimal_places': get_company_value(request.user, c, 'pos_decimal_places'),
        # interface parameters
        'date_format': get_date_format(request.user, c, 'js'),
        'time_format': get_time_format(request.user, c, 'js'),
        'product_button_size': g.PRODUCT_BUTTON_DIMENSIONS[get_user_value(request.user, 'pos_product_button_size')],
        'bill_width': get_user_value(request.user, 'pos_interface_bill_width'),
        'display_breadcrumbs': False, # get_user_value(request.user, 'pos_display_breadcrumbs'), (currently hardcodedly disabled)
        'product_display': get_user_value(request.user, 'pos_product_display'),
    }

    data = {
        # data for selling stuff
        'categories': get_all_categories_structured(c),
        'products': get_all_products(request.user, c),
        'discounts': get_all_discounts(request.user, c, False),
        'contacts': get_all_contacts(request.user, c),
        'taxes':  get_all_taxes(request.user, c),
        'registers': get_all_registers(request.user, c),
        'unit_types': g.UNITS,
        'company': company_to_dict(request.user, c),  # this company's details (will be shown on the receipt)
        # current user  TODO: change when login system changes
        'user_name': str(request.user),  # TODO: specify how user is displayed
        'user_id': request.user.id,
    }

    context = {
        # page properties
        'company': c,
        'title': c.name,
        'site_title': g.MISC['site_title'],

        # template etc.
        'currency': get_company_value(request.user, c, 'pos_currency'),
        'currency_symbol': currencies.currencies[get_company_value(request.user, c, 'pos_currency')][1],
        'sexes': g.SEXES,
        'countries': country_choices,
        'pin_length': g.PIN_LENGTH,

        # user config
        'config': JsonStringify(config),
        'data': JsonStringify(data),
        'registers': data['registers'],
    }

    return render(request, 'pos/terminal.html', context)


@login_required
def save(request, company):
    """ terminal settings on change """
    try:
        width = int(JsonParse(request.POST.get('data')).get('bill_width'))
    except (ValueError, TypeError):
        return JsonError(_("Data error"))

    set_user_value(request.user, 'pos_interface_bill_width', width)

    # save stuff from data to config
    return JsonOk()


@login_required
def lock_session(request, company):
    try:
        c = Company.objects.get(url_name=company)
        return lock_session_(request, c)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))


def lock_session_(request, c):
    # a session is locked for a specific company by adding its url_name
    if 'locked' not in request.session:
        request.session['locked'] = []

    request.session['locked'].append(c.url_name)
    request.session['original_url'] = request.GET.get('next')
    request.session.modified = True

    if request.is_ajax():
        # tell javascript if there's no pin set
        return JsonResponse({'status': 'ok', 'no_pin': request.user.get_permission(c).pin is None})
    else:
        return redirect('pos:locked_session', company=c.url_name)


# ignore locking here or we'll be caught in an infinite redirect loop
@login_required_nolocking
def locked_session(request, company):
    # show the unlock screen
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    context = {
        'no_pin': request.user.get_permission(c).pin is None,
        'company': c,
        'pin_length': g.PIN_LENGTH,
        'message': '',
    }

    return render(request, 'pos/locked.html', context)


# ignore locking here or we'll be caught in an infinite redirect loop
@login_required_nolocking
def unlock_session(request, company):
    switch_data = switch_user(request, company)
    c = switch_data.get('company')

    if switch_data.get('status') == 'ok':
        # redirect to
        user = switch_data.get('user')

        redirect_url = switch_data.get('redirect_url')
        if not redirect_url:
            redirect_url = reverse('pos:terminal', args=(c.url_name,))

        # return the url that we'll redirect to
        # there is no redirecting
        return JsonResponse({
            'status': switch_data.get('status'),
            'user_id': switch_data.get('user').id,
            'user_name': unicode(user),
            'company': c.url_name,  # here, url name is required
            'csrf_token': unicode(csrf(request)['csrf_token']),
            'redirect_url': redirect_url,
        })
    else:  # switching failed for some reason
        return JsonError(switch_data.get('message'))


def switch_user(request, company):
    """
        switches user with PIN in request.POST.
        returns {status, message } if something went wrong or
                { status, user, redirect_url, company } if the user has been switched successfully
    """
    # get the company
    try:
        c = Company.objects.get(url_name=company)
        return switch_user_(request, c)
    except Company.DoesNotExist:
        return {'status': 'error', 'message': _("Company does not exist")}


def switch_user_(request, c):
    # check the user credentials:
    if not request.user.is_authenticated():
        return {'status': 'locked', 'message': _("This session is locked"), 'company': c}

    # check if the user belongs to this company
    try:
        current_permission = request.user.get_permission(c)
    except Permission.DoesNotExist:
        return {'status': 'error', 'message': _("You have no permission for this company"), 'company': c}

    # get the new user using data in request.POST:
    # next: the next url
    # unlock_type: 'pin' | 'password'
    # pin:       | only for unlock_type = 'pin'
    # email:     | only for unlock_type = 'password'
    # password:  | only for unlock_type = 'password'
    try:
        data = JsonParse(request.POST.get('data'))
        if not data:
            raise KeyError
    except (KeyError, ValueError, TypeError):
        return {'status': 'error', 'message': "Invalid request data", 'company': c}

    if data.get('unlock_type') == 'pin':
        # if there's no pin entered, set the current user's pin
        pin = int(data['pin'])

        if not current_permission.pin:
            if not current_permission.create_pin(custom_pin=pin):
                return {'status': 'error', 'message': _("Wrong PIN format")}

        # get a user from current company by entered pin;
        try:
            switched_permission = Permission.objects.get(company=c, pin=pin)
            switched_user = switched_permission.user
        except (Permission.DoesNotExist, TypeError, ValueError):
            return {'status': 'error', 'message': _("Wrong PIN"), 'company': c}
    elif data.get('unlock_type') == 'password':
        # get a user from current company by email and password (achtung! filter by company!)
        # try:
        #     switched_user = BlocklogicUser.objects.get(email=data.get('email'))
        #     switched_permission = Permission.objects.get(user=switched_user, company=c)
        #
        #     if switched_user
        return {'status': 'error', 'message': _("Not implemented"), 'company': c}
    else:
        return {'status': 'error', 'message': _("Unknown unlock type"), 'company': c}

    # TODO: prevent a user with higher privileges to log in using only PIN

    # log the user in
    if not switched_user.is_active:
        return {'status': 'error', 'message': _("This user is not active."), 'company': c}

    # clear this user's session
    redirect_url = request.session.get('original_url')
    request.session['locked'] = []
    request.session.modified = True
    request.session.clear()

    # log out the current user
    django_logout(request)

    # log in the other user
    user = authenticate(username=switched_user.username, password=pin, type='pin', company=c)
    if not user:
        return {'status': 'error', 'message': _("Authentication failed"), 'company': c}

    django_login(request, user)

    return {'status': 'ok',
            'user': switched_user,
            'redirect_url': redirect_url,
            'company': c, }