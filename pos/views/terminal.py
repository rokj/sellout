from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pos.models import Company
from pos.views.manage import get_all_categories_structured

from pos.views.util import has_permission, no_permission_view, JSON_response, JSON_ok, JSON_parse, JSON_error
from config.functions import get_value, set_value
import common.globals as g

import json

### index
@login_required
def terminal(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # see if user has permissions to use/see this terminal
    if not has_permission(request.user, c, 'terminal', 'list'):
        return no_permission_view(request, c, _("visit this page"))
    
    context = {
        'company':c,
        'title':c.name,
        'site_title':g.MISC['site_title'],
    }
    return render(request, 'pos/terminal.html', context)

def terminal_init(request, company):
    try:
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    """ return all terminal settings and other static data in JSON format """
    data = {
        # user's data
        'categories':get_all_categories_structured(c, data=[]),
        # interface parameters
        'interface':get_value(request.user, 'pos_interface'),
        'product_button_size':g.PRODUCT_BUTTON_DIMENSIONS[get_value(request.user, 'pos_interface_product_button_size')],
        'bill_width':get_value(request.user, 'pos_interface_bill_width'),
        # urls for various things
        'search_products_url':reverse('pos:search_products', args={company:c.url_name}),
        'exit_url':reverse('pos:terminal_exit', args={company:c.url_name}),
    }
    return JSON_response(data)

def terminal_exit(request, company):
    """ save stuff when the terminal page closes/unloads """
    data = JSON_parse(request.POST.get('data'))

    if data.get('bill_width'):
        print data.get('bill_width')
        set_value(request.user, 'pos_interface_bill_width', int(data['bill_width']))

    # save stuff from data to config
    return JSON_ok()