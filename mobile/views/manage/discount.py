# author: nejc jurkovic
# date: 9. 8. 2013
#
# Views for managing POS data: discounts
import datetime as dtm
from decimal import Decimal
from django.utils.translation import ugettext as _
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from pos.models import Company
from pos.views.manage import discount
from pos.views.manage.discount import discount_to_dict
from pos.views.util import JSON_error, has_permission, JSON_response, JSON_ok, JSON_parse, parse_date
from pos.models import Discount

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_discounts(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    if not has_permission(request.user, c, 'discount', 'list'):
        return JSON_error(_("You have no permission to view taxes"))

    discounts = Discount.objects.filter(company=c)

    r = []
    for d in discounts:
        r.append(discount_to_dict(request.user, d, android=True))

    return JSON_ok(extra=r)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_discount(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # check permissions: needs to be at least manager

    if not has_permission(request.user, c, 'discount', 'edit'):
        return JSON_error(_("You have no permission to view taxes"))

    data = JSON_parse(request.POST['data'])

    try:
        d = Discount.objects.get(id=data['id'])
    except Discount.DoesNotExist:
        return JSON_error(_("Discount does not exist"))

    if not request.user.has_perm('pos.delete_discount'):
        return JSON_error(_("You have no permission to delete discounts."))

    d.delete()

    return JSON_ok(extra=discount_to_dict(request.user, d, android=True))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_discount(request, company):
    # edit an existing contact
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))


    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return JSON_error(_("edit discounts"))

    data = JSON_parse(request.POST['data'])

    try:
        d = Discount.objects.get(id=data['id'])
    except Discount.DoesNotExist:
        return JSON_error(_("Discount does not exist"))

    # check if contact actually belongs to the given company
    if d.company != c:
        return JSON_error(_("failed"))


        # check if user has permissions to change contacts
    if not request.user.has_perm('pos.change_discount'):
        return JSON_error(_("You have no permission to edit discounts."))

    if request.method == 'POST':
        # submit data
        start_date = data.get('start_date')
        if start_date:
            start = dtm.date(year=start_date[0], month=start_date[1],
                                 day=start_date[2])
        else:
            start=None

        end_date = data.get('end_date')
        if end_date:
            end = dtm.date(year=end_date[0], month=end_date[1],
                                 day=end_date[2])
        else:
            end=None
        d.description = data.get('description')
        d.code = data.get('code')
        d.type = data.get('type')
        d.amount = Decimal(data.get('amount'))
        d.start_date = start
        d.end_date = end
        d.active = data.get('active')
        d.save()

    return JSON_ok(extra=discount_to_dict(request.user, c, d, android=True))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_add_discount(request, company):
    # edit an existing contact
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return JSON_error(_("add discounts"))


    # check for permission for adding discounts
    if not request.user.has_perm('pos.add_discount'):
        return JSON_error(request, _("You have no permission to add discounts."))

    data = JSON_parse(request.POST['data'])
    start_date = data.get('start_date')
    if start_date:
        start = dtm.date(year=start_date[0], month=start_date[1],
                             day=start_date[2])
    else:
        start=None

    end_date = data.get('end_date')
    if end_date:
        end = dtm.date(year=end_date[0], month=end_date[1],
                             day=end_date[2])
    else:
        end=None

    d = Discount(
        description = data.get('description'),
        code = data.get('code'),
        type = data.get('type'),
        amount = Decimal(data.get('amount')),
        start_date = start,
        end_date = end,
        enabled = data.get('enabled'),
        created_by = request.user,
        company = c
    )
    d.save()

    return JSON_ok(extra=discount_to_dict(request.user, c, d, android=True))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_list_discounts(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'discount', 'list'):
        return JSON_error(_("view discounts"))

    discounts = Discount.objects.filter(company__id=c.id)

    results_display = False

    data = JSON_parse(request.POST['data'])

    # show the filter form
    if request.method == 'POST':

        if data.get('search'):
            discounts = discounts.filter(description__icontains=data['search']) | \
                        discounts.filter(code__icontains=data['search'])

        # start_date
        if data.get('start_date'):
            # parse date first
            start_date = data.get('start_date')
            start = dtm.date(year=start_date[0], month=start_date[1],
                             day=start_date[2])

            discounts = discounts.filter(start_date__gte=start)

        # end_date
        if data.get('end_date'):
            end_date = data.get('end_date')
            end = dtm.date(year=start_date[0], month=start_date[1],
                             day=start_date[2])

            discounts = discounts.filter(end_date__lse=end)

        # active
        if data.get('active') is not None:
            discounts = discounts.filter(active=data['active'])

        results_display = True  # search results are being displayed


    r = []
    for d in discounts:
        r.append(discount_to_dict(request.user, c, d, android=True))

    return JSON_ok(extra=r)
