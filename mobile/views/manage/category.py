from django.http import JsonResponse
from django.utils.translation import ugettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Company, Category
from pos.views.manage.category import get_category, validate_category, \
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
        c = Company.objects.get(url_name = company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # sellers can add category
    if not has_permission(request.user, c, 'category', 'edit'):
        return JsonError(_("You have no permission to add products"))

    data = JsonParse(request.POST['data'])

    # validate data
    valid = validate_category(request.user, c, data)
    if not valid['status']:
        return JsonError(valid['message'])
    data = valid['data']

    parent = data['parent']

    color = data.get('color')
    if not color:
        color = g.CATEGORY_COLORS[0]

    # save category:
    category = Category(
        company=c,
        parent=parent,
        name=data['name'],
        description=data['description'],
        color=color,
        created_by=request.user,
    )
    category.save()

    # add image, if it's there

    #if data.get('change_image') == True:
    #    if data['image']: # new image is uploade

    #        if category.image:
    #            category.image.delete()
    #        # save a new image
    #
    #         category.image = data['image']
    #
    #     else: # delete the old image
    #         category.image.delete()

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

    valid = validate_category(request.user, c, data)

    if not valid['status']:
        return JsonError(valid['message'])

    form = valid['form']
    category = form.save()

    return JsonOk(extra=category_to_dict(category, android=True))


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_delete_category(request, company):
    return delete_category(request, company)


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def mobile_get_category(request, company, category_id):
    return get_category(request, company, category_id)


def mobile_JSON_dump_categories(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    cat = Category.objects.filter(company__id=c.id)
    return JsonOk(extra="")