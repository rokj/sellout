from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from pos.models import Company
from pos.views.manage.category import get_all_categories_structured
from pos.views.manage.company import company_to_dict
from pos.views.manage.contact import get_all_contacts
from pos.views.manage.discount import get_all_discounts
from pos.views.manage.product import get_all_products

from pos.views.util import has_permission, no_permission_view, JSON_ok, JSON_parse, JSON_stringify
from config.functions import get_user_value, set_user_value, get_date_format, get_time_format, get_company_value
import common.globals as g

import settings


### index
@login_required
def terminal(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # see if user has permissions to use/see this terminal
    if not has_permission(request.user, c, 'terminal', 'list'):
        return no_permission_view(request, c, _("visit this page"))

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
        'interface': get_user_value(request.user, 'pos_interface'),
        'product_button_size': g.PRODUCT_BUTTON_DIMENSIONS[get_user_value(request.user, 'pos_interface_product_button_size')],
        'bill_width': get_user_value(request.user, 'pos_interface_bill_width'),
        'display_breadcrumbs': get_user_value(request.user, 'pos_display_breadcrumbs'),
        'product_display': get_user_value(request.user, 'pos_product_display'),
        #'printer_port': get_value(request.user, 'pos_printer_port'),
        'receipt_size': 'small',
        'printer_driver': 'system'
    }

    data = {
        # data for selling stuff
        'categories': get_all_categories_structured(c),
        'products': get_all_products(request.user, c),
        'discounts': get_all_discounts(request.user, c, False),
        'contacts': get_all_contacts(request.user, c),
        'taxes':  [], #get_all_taxes(request.user, c), TODO
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

        # user config
        'config': JSON_stringify(config, True),
        'data': JSON_stringify(data, True),
    }
    return render(request, 'pos/terminal.html', context)


@login_required
def save(request, company):
    """ save stuff when the terminal page closes/unloads """
    data = JSON_parse(request.POST.get('data'))

    if data.get('bill_width'):
        set_user_value(request.user, 'pos_interface_bill_width', int(data['bill_width']))

    # save stuff from data to config
    return JSON_ok()
