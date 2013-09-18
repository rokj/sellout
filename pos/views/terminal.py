from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from pos.models import Company
from pos.views.util import has_permission, no_permission_view
import common.globals as g

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

def other_view():
    pass