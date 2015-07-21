import json
from django.db.models import Q
from django.utils.translation import ugettext as _

from common.decorators import login_required
from common.functions import JsonError, has_permission, JsonParse, JsonOk
from registry.models import ContactRegistry
from pos.models import Company, Contact
from pos.views.manage.contact import contact_to_dict


@login_required
def get_contacts(request, company):
    """
        creates contact on the fly (while creating bill on the terminal)
        contact data is in request.POST
    """
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist."))

    # permissions
    if not has_permission(request.user, c, 'contact', 'edit'):
        return JsonError(_("You have no permission to add contacts"))

    data = JsonParse(request.POST.get('data'))

    my_contacts = Contact.objects.filter(
        Q(company_name__icontains=data['search_term']) |
        Q(first_name__icontains=data['search_term']) |
        Q(last_name__icontains=data['search_term']) |
        Q(street_address__icontains=data['search_term']) |
        Q(postcode__icontains=data['search_term']) |
        Q(city__icontains=data['search_term']) |
        Q(state__icontains=data['search_term']) |
        Q(country__icontains=data['search_term']) |
        Q(email__icontains=data['search_term']) |
        Q(vat__icontains=data['search_term']),
        company=c,
    )

    durs_contacts = ContactRegistry.objects.filter(
        Q(company_name__icontains=data['search_term']) |
        Q(first_name__icontains=data['search_term']) |
        Q(last_name__icontains=data['search_term']) |
        Q(street_address__icontains=data['search_term']) |
        Q(postcode__icontains=data['search_term']) |
        Q(city__icontains=data['search_term']) |
        Q(state__icontains=data['search_term']) |
        Q(country__icontains=data['search_term']) |
        Q(email__icontains=data['search_term']) |
        Q(vat__icontains=data['search_term'])
    )

    my_contacts = json.dumps([contact_to_dict(request.user, c, mc) for mc in my_contacts])
    durs_contacts = json.dumps([contact_to_dict(request.user, c, dc) for dc in durs_contacts])

    return JsonOk(extra={"my_contacts": my_contacts, "durs_contacts": durs_contacts})