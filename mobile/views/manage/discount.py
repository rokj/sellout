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
from pos.views.manage.discount import discount_to_dict, validate_discount
from pos.views.util import JsonError, has_permission, JsonOk, JsonParse
from pos.models import Discount

@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_discounts(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    if not has_permission(request.user, c, 'discount', 'list'):
        return JsonError(_("You have no permission to view taxes"))

    discounts = Discount.objects.filter(company=c)

    r = []
    for d in discounts:
        r.append(discount_to_dict(request.user, c, d, android=True))

    return JsonOk(extra=r)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_delete_discount(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be at least manager

    if not has_permission(request.user, c, 'discount', 'edit'):
        return JsonError(_("You have no permission to view taxes"))

    data = JsonParse(request.POST['data'])

    try:
        d = Discount.objects.get(id=data['id'])
    except Discount.DoesNotExist:
        return JsonError(_("Discount does not exist"))

    if not request.user.has_perm('pos.delete_discount'):
        return JsonError(_("You have no permission to delete discounts."))

    d.delete()

    return JsonOk(extra=discount_to_dict(request.user, c, d, android=True))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_edit_discount(request, company):
    # edit an existing contact
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return JsonError(_("edit discounts"))

    data = JsonParse(request.POST['data'])

    try:
        d = Discount.objects.get(id=data['id'])
    except Discount.DoesNotExist:
        return JsonError(_("Discount does not exist"))

    # check if contact actually belongs to the given company
    if d.company != c:
        return JsonError(_("failed"))

    if request.method == 'POST':

        data = JsonParse(request.POST['data'])
        valid = validate_discount(data,request.user, c, android=True, discount=d)

        if not valid.get('status'):
            return JsonError(valid['message'])

        form = valid['form']
        d = Discount(
                description=form.cleaned_data.get('description'),
                code=form.cleaned_data.get('code'),
                type=form.cleaned_data.get('type'),
                amount=form.cleaned_data.get('amount'),
                start_date=form.cleaned_data.get('start_date'),
                end_date=form.cleaned_data.get('end_date'),
                enabled=form.cleaned_data.get('enabled'),
                created_by=request.user,
                company=c
            )
        d.save()

        return JsonOk(extra=discount_to_dict(request.user, c, d, android=True))



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_add_discount(request, company):
    # edit an existing contact
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, 'discount', 'edit'):
        return JsonError(_("add discounts"))


    # check for permission for adding discounts
    if not request.user.has_perm('pos.add_discount'):
        return JsonError(_("You have no permission to add discounts."))

    data = JsonParse(request.POST['data'])

    valid = validate_discount(data, request.user, c, android=True)

    if not valid.get('status'):
        return JsonError(valid['message'])

    form = valid['form']
    d = Discount(
                description=form.cleaned_data.get('description'),
                code=form.cleaned_data.get('code'),
                type=form.cleaned_data.get('type'),
                amount=form.cleaned_data.get('amount'),
                start_date=form.cleaned_data.get('start_date'),
                end_date=form.cleaned_data.get('end_date'),
                enabled=form.cleaned_data.get('enabled'),

                created_by=request.user,
                company=c
            )
    d.save()

    return JsonOk(extra=discount_to_dict(request.user, c, d, android=True))


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_list_discounts(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'discount', 'view'):
        return JsonError(_("view discounts"))

    discounts = Discount.objects.filter(company__id=c.id)

    results_display = False

    data = JsonParse(request.POST['data'])

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
            end = dtm.date(year=end_date[0], month=end_date[1],
                             day=end_date[2])

            discounts = discounts.filter(end_date__lse=end)

        # active
        if data.get('active') is not None:
            discounts = discounts.filter(active=data['active'])

        results_display = True  # search results are being displayed


    r = []
    for d in discounts:
        r.append(discount_to_dict(request.user, c, d, android=True))

    return JsonOk(extra=r)
