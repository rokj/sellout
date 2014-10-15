# this file should be named register.py, but would be confused with user registration, so here's a synonym
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from pos.models import Register, Company
from pos.views.manage.till import get_all_registers
from pos.views.util import has_permission, no_permission_view, manage_delete_object, JsonOk

from common import globals as g
from config.functions import get_date_format, get_user_value, get_company_value


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_get_all_registers(request, company):
    user = request.user

    c = Company.objects.get(url_name=company)

    return JsonOk(extra=get_all_registers(c, user))

"""
@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def list_registers(request, company):
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'register', 'list'):
        return no_permission_view(request, c, _("view registers"))
    
    context = {
        'company': c,
        'title': _("Cash Registers"),
        'registers': Register.objects.filter(company__id=c.id).order_by('name'),
        'site_title': g.MISC['site_title'],
        'date_format_django': get_date_format(request.user, c, 'django'),
        'date_format_js': get_date_format(request.user, c, 'js'),
        'currency': get_company_value(request.user, c, 'pos_currency'),
    }

    return render(request, 'pos/manage/tills.html', context)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def add_register(request, company):
    # add a new register
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'register', 'edit'):
        return no_permission_view(request, c, _("add registers"))

    context = {
        'add': True,
        'company': c,
        'title': _("Add register"),
        'site_title': g.MISC['site_title'],
        'date_format_js': get_date_format(request.user, c, 'js')
    }

    if request.method == 'POST':
        # submit data
        form = RegisterForm(request.POST)
        form.user = request.user
        form.company = c

        if form.is_valid():
            # create a new Register
            register = Register(
                name=form.cleaned_data.get('name'),
                receipt_format=form.cleaned_data.get('receipt_format'),
                receipt_type=form.cleaned_data.get('receipt_type'),
                print_logo=form.cleaned_data.get('print_logo'),
                location=form.cleaned_data.get('location'),
                print_location=form.cleaned_data.get('print_location'),

                created_by=request.user,
                company=c
            )
            register.save()

            return redirect('pos:list_registers', company=c.url_name)
    else:
        form = RegisterForm()
        form.user = request.user
        form.company = c

    context['form'] = form

    return render(request, 'pos/manage/till.html', context)


def edit_register(request, company, register_id):
    # edit an existing register
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

    return render(request, 'pos/manage/till.html', context)


@login_required
def delete_register(request, company):
    return manage_delete_object(request, company, Register,
                                (_("You have no permission to delete registers"), _("Could not delete register")))

"""