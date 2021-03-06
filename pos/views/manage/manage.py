# author: nejc jurkovic
# date: 3. 9. 2013
#
# Views for managing POS data: home
from django.shortcuts import get_object_or_404, render
from common.decorators import login_required
from django.utils.translation import ugettext as _

from pos.models import Company
from common.functions import has_permission, no_permission_view
import common.globals as g

###################
### manage home ###
###################
@login_required
def manage_home(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # see if user has permission to view or edit management stuff
    if not has_permission(request.user, c, 'manage', 'view'):
        return no_permission_view(request, c, _("You have no permission to manage POS settings."))
    
    context = {
        'title': _("Management"),
        'site_title': g.MISC['site_title'],
        'company': c,
    }
    
    return render(request, 'pos/manage/manage.html', context)