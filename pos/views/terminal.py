from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from pos.models import Company
from pos.views.manage import get_all_categories_structured

from pos.views.util import has_permission, no_permission_view
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
        'categories':get_all_categories_structured(c, data=[]),
    }) # these characters need escaping:  
    data = data.replace("<","&lt;") # < becomes &lt;
    data = data.replace(">","&lt;") # > becomes &gt;
    data = data.replace("&","&amp;") # & becomes &amp;# otherwise, a </script> in data will render the entire page useless.
    
    context = {
        'company':c,
        'title':c.name,
        'site_title':g.MISC['site_title'],
        'data':data,
        
    }
    return render(request, 'pos/terminal.html', context)

