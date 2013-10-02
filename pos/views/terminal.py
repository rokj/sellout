from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pos.models import Company
from pos.views.manage import get_all_categories_structured

from pos.views.util import has_permission, no_permission_view
from config.functions import get_value
import common.globals as g

import json

### index
@login_required
def terminal(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # see if user has permissions to use/see this terminal
    if not has_permission(request.user, c, 'terminal', 'list'):
        return no_permission_view(request, c, _("visit this page"))
    
    data = json.dumps({ # javascript 'constants' (printed {{data}} in javascript)
        'interface':get_value(request.user, 'pos_interface'),
        'product_button_size':g.PRODUCT_BUTTON_DIMENSIONS[get_value(request.user, 'pos_interface_product_button_size')],
        'categories':get_all_categories_structured(c, data=[]),
        'search_products_url':reverse('pos:search_products', args={company:c.url_name}),
    }) # these characters need escaping:  
    data = data.replace("<","&lt;") # < becomes &lt;
    data = data.replace(">","&gt;") # > becomes &gt;
    data = data.replace("&","&amp;") # & becomes &amp;
    # otherwise, a </script> in data will render the entire page useless.
    
    context = {
        'company':c,
        'title':c.name,
        'site_title':g.MISC['site_title'],
        'data':data,
        
    }
    return render(request, 'pos/terminal.html', context)

