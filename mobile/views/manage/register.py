# this file should be named register.py, but would be confused with user registration, so here's a synonym
from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Register, Company
from pos.views.manage.register import get_all_registers, validate_register, register_to_dict
from pos.views.util import has_permission, no_permission_view, manage_delete_object, JsonOk, JsonError, JsonParse

from common import globals as g
from config.functions import get_date_format, get_user_value, get_company_value



@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def list_registers(request, company):
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    user = request.user

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'register', 'view'):
        return JsonError(_("You have no permission to view registers"))


    data = get_all_registers(c, user)

    return JsonOk(extra=data, safe=False)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_add_register(request, company):
    # add a new register
    try:
        c = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'register', 'edit'):
        return JsonError(_("You have no permission to edit registers"))

    data = JsonParse(request.POST['data'])

    valid = validate_register(request.user, c, data)

    if not valid.get('status'):
        return JsonError(valid['message'])

    form = valid['form']
    register = form.save(False)
    register.company = c
    register.created_by = request.user

    register = form.save()

    return JsonOk(extra=register_to_dict(register))


def mobile_edit_register(request, company, register_id):
    # edit an existing register

    return
    """
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'register', 'edit'):
        return no_permission_view(request, c, _("edit registers"))

    context = {
        'company': c,
        'register_id': register_id,
        'title': _("Edit register"),
        'site_title': g.MISC['site_title'],
        'date_format_js': get_date_format(request.user, c, 'js'),
    }

    # get register
    register = get_object_or_404(Register, id=register_id, company=c)

    if request.method == 'POST':
        # submit data
        form = RegisterForm(request.POST)
        form.user = request.user
        form.company = c

        if form.is_valid():
            register.name= form.cleaned_data.get('name')
            register.receipt_format = form.cleaned_data.get('receipt_format')
            register.receipt_type = form.cleaned_data.get('receipt_type')
            register.print_logo = form.cleaned_data.get('print_logo')
            register.location = form.cleaned_data.get('location')
            register.print_location = form.cleaned_data.get('print_location')

            register.save()

            return redirect('pos:list_registers', company=c.url_name)
    else:
        initial = register_to_dict(request.user, c, register)
        form = RegisterForm(initial=initial)
        form.user = request.user
        form.company = c

    context['form'] = form

    return render(request, 'pos/manage/register.html', context)"""


@login_required
def delete_register(request, company):
    return manage_delete_object(request, company, Register,
                                (_("You have no permission to delete registers"), _("Could not delete register")))

