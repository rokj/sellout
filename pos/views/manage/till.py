from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from pos.models import Register, Company
from pos.views.util import error, JSON_response, JSON_error, \
                           has_permission, no_permission_view, \
                           format_number, format_date, parse_date, parse_decimal, \
                           max_field_length

from common import globals as g
from config.functions import get_date_format, get_user_value, get_company_value


#############
### views ###
#############
class RegisterForm(forms.ModelForm):
    class Meta:
        model = Register
        # unused fields (will be added programatically)
        exclude = [
            'created_by',
            'updated_by',
            'company']


@login_required
def registers(request, company):
    c = get_object_or_404(Company, url_name=company)
    
    # check permissions: needs to be guest
    if not has_permission(request.user, c, 'register', 'list'):
        return no_permission_view(request, c, _("view registers"))
    
    r = Register.objects.filter(company__id=c.id)

    context = {
        'company': c,
        'title': _("Cash Registers"),
        'registers': r,
        'empty_form': RegisterForm(),
        'site_title': g.MISC['site_title'],
        'date_format_django': get_date_format(request.user, c, 'django'),
        'date_format_js': get_date_format(request.user, c, 'js'),
        'currency': get_company_value(request.user, c, 'pos_currency'),
    }

    return render(request, 'pos/manage/registers.html', context)
