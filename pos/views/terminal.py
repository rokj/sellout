from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from pos.models import Company, Register, Bill
from pos.views.bill import bill_to_dict
from pos.views.manage.category import get_all_categories_structured
from pos.views.manage.company import company_to_dict
from pos.views.manage.contact import get_all_contacts
from pos.views.manage.discount import get_all_discounts
from pos.views.manage.product import get_all_products
from pos.views.manage.tax import get_all_taxes
from pos.views.manage.till import get_all_registers

from pos.views.util import has_permission, no_permission_view, JsonOk, JsonParse, JsonStringify, error, JsonError
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

    # terminal settings and other data in JSON (will be put into javascript globals)
    if get_company_value(request.user, c, 'pos_discount_calculation') == 'Tax first':
        tax_first = True
    else:
        tax_first = False

    config = {
        # user's data
        'currency': get_company_value(request.user, c, 'pos_currency'),
        'separator': get_company_value(request.user, c, 'pos_decimal_separator'),
        'decimal_places': get_company_value(request.user, c, 'pos_decimal_places'),
        'tax_first': tax_first,
        # interface parameters
        'date_format': get_date_format(request.user, c, 'js'),
        'time_format': get_time_format(request.user, c, 'js'),
        'product_button_size': g.PRODUCT_BUTTON_DIMENSIONS[get_user_value(request.user, 'pos_product_button_size')],
        'bill_width': get_user_value(request.user, 'pos_interface_bill_width'),
        'display_breadcrumbs': False, # get_user_value(request.user, 'pos_display_breadcrumbs'), (currently hardcodedly disabled)
        'product_display': get_user_value(request.user, 'pos_product_display'),
        # registers and printers
        #'printer_port': get_value(request.user, 'pos_printer_port'),
        'receipt_size': 'small',
        'printer_driver': 'system',
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
        'company': company_to_dict(c),  # this company's details (will be shown on the receipt)
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
        'sexes': g.SEXES,
        'countries': country_choices,

        # user config
        'config': JsonStringify(config, True),
        'data': JsonStringify(data, True),
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
def set_register(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist."))

    # the user must have view permissions for terminal
    if not has_permission(request.user, c, 'terminal', 'view'):
        return JsonError(_("Permission denied"))

    # get the number and
    try:
        id = int(JsonParse(request.POST.get('data')).get('register_id'))
    except (ValueError, TypeError):
        return JsonError("Data error")

    return JsonOk()
