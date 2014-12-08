# this file should be named register.py, but would be confused with user registration, so here's a synonym
from django.db.models import FieldDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from common.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms

from pos.models import Register, Company
from pos.views.util import has_permission, no_permission_view, manage_delete_object

from common import globals as g
from config.functions import get_date_format, get_user_value, get_company_value


def register_to_dict(user, company, register):
    """ company and user are not needed at the moment (maybe for displaying dates/times in the future) """
    r = {
        'id': register.id,
        'name': register.name,

        'receipt_format_display': register.get_receipt_format_display(),
        'receipt_format': register.receipt_format,

        'receipt_type_display': register.get_receipt_type_display(),
        'receipt_type': register.receipt_type,

        'print_logo': register.print_logo,

        'location': register.location,
        'print_location': register.print_location,
    }

    try:  # fields that are not common to Register and BillRegister
        r['printer_driver'] = register.printer_driver
        r['printer_driver_display'] = register.get_printer_driver_display()
    except (FieldDoesNotExist, AttributeError):
        pass

    return r


def get_all_registers(user, company):
    all_registers = Register.objects.filter(company=company)

    r = []

    for register in all_registers:
        r.append(register_to_dict(user, company, register))

    return r


#############
### views ###
#############

def validate_register(user, company, data, register=None):
    """ return:
    {status:true/false - if cleaning succeeded
     data:cleaned_data - empty dict if status = false
     message:error_message - empty if status = true """

    if register:
        form = RegisterForm(data=data, instance=register)
    else:
        form = RegisterForm(data=data)
        if 'device_id' in data:
            try:
                Register.objects.get(company=company, device_id=data.get('device_id'))
                return {'status': False, 'data': None, 'message': _('Device with this id already exists')}
            except Register.DoesNotExist:
                pass

    if form.is_valid():
        return {'status': True, 'message': None, 'form': form}
    else:
        message = form.errors.as_data().itervalues().next()[0].message
        return {'status': False, 'data': None, 'message': message}


class RegisterForm(forms.ModelForm):
    class Meta:
        model = Register
        # unused fields (will be added within view)
        exclude = [
            'created_by',
            'updated_by',
            'company']

        widgets = {
            'print_logo': forms.Select(choices=((True, _("Yes")), (False, _("No")))),
            'print_location': forms.Select(choices=((True, _("Yes")), (False, _("No")))),
        }


@login_required
def list_registers(request, company):
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'register', 'view'):
        return no_permission_view(request, c, _("You have no permission to view registers."))
    
    context = {
        'company': c,
        'title': _("Cash Registers"),
        'registers': Register.objects.filter(company__id=c.id).order_by('name'),
        'site_title': g.MISC['site_title'],
        'date_format_django': get_date_format(request.user, c, 'django'),
        'date_format_js': get_date_format(request.user, c, 'js'),
        'currency': get_company_value(request.user, c, 'pos_currency'),
    }

    return render(request, 'pos/manage/registers.html', context)


@login_required
def add_register(request, company):
    # add a new register
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be manager
    if not has_permission(request.user, c, 'register', 'edit'):
        return no_permission_view(request, c, _("You have no permission to add registers."))

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

        if form.is_valid():
            register = form.save(False)
            register.company = c
            register.created_by = request.user
            register.save()

            return redirect('pos:list_registers', company=c.url_name)
    else:
        form = RegisterForm()
        form.user = request.user
        form.company = c

    context['form'] = form

    return render(request, 'pos/manage/register.html', context)


def edit_register(request, company, register_id):
    # edit an existing register
    c = get_object_or_404(Company, url_name=company)

    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'register', 'edit'):
        return no_permission_view(request, c, _("You have no permission to edit registers."))

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
        form = RegisterForm(request.POST, instance=register)

        if form.is_valid():
            form.save()

        return redirect('pos:list_registers', company=c.url_name)
    else:
        initial = register_to_dict(request.user, c, register)
        form = RegisterForm(initial=initial)
        form.user = request.user
        form.company = c

    context['form'] = form

    return render(request, 'pos/manage/register.html', context)


@login_required
def delete_register(request, company):
    return manage_delete_object(request, company, Register,
                                (_("You have no permission to delete registers"), _("Could not delete register")))