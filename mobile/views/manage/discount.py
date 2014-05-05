# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: discounts
from django.utils.translation import ugettext as _
from pos.models import Company
from pos.views.manage.discount import discount_to_dict
from pos.views.util import JSON_error, has_permission, JSON_response, JSON_ok
from pos.models import Discount

def mobile_get_discounts(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    if not has_permission(request.user, c, 'tax', 'list'):
        return JSON_error(_("You have no permission to view taxes"))

    discounts = Discount.objects.filter(company=c)

    r = []
    for d in discounts:
        r.append(discount_to_dict(request.user, d))

    return JSON_ok(extra=r)

