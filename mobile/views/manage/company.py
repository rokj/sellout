# TODO
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from pos.models import Company
from pos.views.manage.company import company_to_dict, CompanyForm, validate_company, save_color_image, \
    save_monochrome_image
from pos.views.util import JSON_error, JSON_ok, has_permission, JSON_parse
from django.utils.translation import ugettext as _


@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def get_company(request, company):

    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    return JSON_ok(extra=company_to_dict(c, android=True))

@api_view(['POST', 'GET'])
@permission_classes((IsAuthenticated,))
def edit_company(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JSON_error(_("Company does not exist"))

    if not has_permission(request.user, c, 'company', 'edit'):
        return JSON_error(message=_("edit company details"))

    data = JSON_parse(request.POST['data'])

    validate_data = validate_company(request.user, c, data)
    if validate_data['status']:
        data = validate_data['data']
    else:
        return JSON_error(message=validate_data['message'])

    c.name = data.get('name')
    c.url_name = data.get('url_name')
    c.email = data.get('email')
    c.postcode = data.get('postcode')
    c.city = data.get('city')
    c.state = data.get('state')
    c.phone = data.get('phone')
    c.vat_no = data.get('vat_no')
    c.website = data.get('website')
    c.notes = data.get('notes')

    if data.get('change_color_logo'):
        if data.get('color_logo'):
            d = {'image': data.get('color_logo')}
            save_color_image(c, d)
        else:
            save_color_image(c, {})

    if data.get('change_monochrome_logo'):
        if data.get('monochrome_logo'):
            d = {'image': data.get('monochrome_logo')}
            save_monochrome_image(c, d)
        else:
            save_monochrome_image(c, {})

    c.save()

    return JSON_ok(extra=company_to_dict(c, android=True))

