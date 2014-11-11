from django.http import JsonResponse
from django.utils.translation import ugettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Company, Category
from pos.views.manage.category import validate_category, \
    get_all_categories_structured, category_to_dict, validate_parent, delete_category
from pos.views.util import JsonError, JsonParse, JsonOk, \
    has_permission
from common import globals as g



#############
### views ###
#############

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_JSON_categories_strucutred(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'category', 'view'):
        return JsonError("no permission")

    # return all categories' data in JSON format
    return JsonResponse(get_all_categories_structured(c, sort='name', android=True), safe=False)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_JSON_categories(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # permissions
    if not has_permission(request.user, c, 'category', 'view'):
        return JsonError("no permission")
    data = []
    category = Category.objects.filter(company=c)

    for c in category:
        data.append(category_to_dict(c, android=True))

    # return all categories' data in JSON format
    return JsonResponse(data, safe=False)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_add_category(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    if not has_permission(request.user, c, 'category', 'edit'):
        return JsonError(_("You have no permission to edit products"))

    data = JsonParse(request.POST['data'])
    # data['company'] = c
    valid = validate_category(request.user, c, data)

    if not valid.get('status'):
        return JsonError(valid['message'])

    form = valid['form']
    category = form.save(False)

    if 'created_by' not in form.cleaned_data:
        category.created_by = request.user
    if 'company_id' not in form.cleaned_data:
        category.company_id = c.id

    category = form.save()

    return JsonOk(extra=category_to_dict(category, android=True))


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_edit_category(request, company):

    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    if not has_permission(request.user, c, 'category', 'edit'):
        return JsonError(_("You have no permission to edit products"))

    data = JsonParse(request.POST['data'])
    # data['company'] = c
    valid = validate_category(request.user, c, data)

    if not valid.get('status'):
        return JsonError(valid['message'])

    form = valid['form']
    category = form.save()

    return JsonOk(extra=category_to_dict(category, android=True))


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_delete_category(request, company):
    return delete_category(request, company)


def mobile_JSON_dump_categories(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    cat = Category.objects.filter(company__id=c.id)
    return JsonOk(extra="")