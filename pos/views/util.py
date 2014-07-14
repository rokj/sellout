from django.db.backends.dummy.base import IntegrityError
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.http import HttpResponse

from common import globals as g
from config.functions import get_date_format, get_time_format, get_company_value
from pos.models import Permission, Company

import json
from decimal import Decimal
from datetime import datetime


# requests and responses
def error(request, company, message):
    
    context = {
        'company': company,
        'message': message,
        'title': _("Error"),
        'site_title': g.MISC['site_title'],
        'back_link': request.build_absolute_uri(),
    }

    return render(request, 'pos/error.html', context)


def JSON_stringify(data, for_javascript=False):
    s = json.dumps(data)

    if for_javascript:
        # this data will be thrown directly into javascript;
        # prevent things like </script> being written into the code
        s = s.replace('/', '\/')

        return s
    else:
        return s


def JSON_response(data):
    return HttpResponse(JSON_stringify(data), mimetype="application/json")


def JSON_error(message):
    return JSON_response({'status': 'error', 'message': message})


def JSON_ok(extra=None):
    data = {'status': 'ok'}
    if extra:
        data['data'] = extra

    return JSON_response(data)


def JSON_parse(string_data):
    try:
        return json.loads(string_data)
    except:
        return None


# misc
def max_field_length(model, field_name):
    return model._meta.get_field(field_name).max_length


# numbers
def format_number(user, company, n, high_precision=False):
    """ returns formatted decimal number n;
        strips zeros, but leaves <p> numbers after decimal point even if they are zero
    """
    sep = get_company_value(user, company, 'pos_decimal_separator')
    p = int(get_company_value(user, company, 'pos_decimal_places'))
    
    if not n:
        return '0'
    
    if high_precision:
        s = str(n.quantize(Decimal('1.'+'0'*8)))  # for calculation, use more decimal places
    else:
        s = str(n.quantize(Decimal('1.'+'0'*p)))
    
    return s.replace('.', sep)


def format_date(user, company, date, send_to='python'):
    """ formats date for display according to user's settings """
    if not date:
        return ''
    else:
        return date.strftime(get_date_format(user, company, send_to))


def format_time(user, company, date):
    """ formats time for display according to user's settings """
    if not date:
        return ''
    else:
        return date.strftime(get_time_format(user, company, 'python'))


def parse_decimal(user, company, string, max_digits=None):
    """ replace user's decimal separator with dot and parse
        return dictionary with result status and parsed number:
        
        {'success':True/False, number:<num>/None}
    """
    
    if user:  # if user is None, try with the dot (user should never be None -
              # this is to avoid checking on every function call)
        string = string.replace(get_company_value(user, company, 'pos_decimal_separator'), '.')
    
    # check for entries too big
    if max_digits:
        if string.find('.') == -1: # it's an integer, it has no 'decimal point'
            if len(string) > max_digits:
                return {'success':False, 'number':None}
        if string.find('.') > max_digits: # it's a float, the integer part shouldn't be longer than max_digits
            return {'success':False, 'number':None}
    
    try:
        number = Decimal(string)
        return {'success':True, 'number':number}
    except:
        return {'success':False, 'number':None}


def parse_date(user, company, string):
    """ parses date in string according to user selected preferences
        return dictionary with result status and parsed datetime:
        
        {'success':True/False, date:<num>/None}
    """
    try:
        d = datetime.strptime(string, get_date_format(user, company, 'python'))
    except:
        return {'success': False, 'date': None}
   
    return {'success': True, 'date': d}


# permissions: cached
def permission_cache_key(user, company):
        return "permission_" + str(user.id) + "_" + str(company.id)


def has_permission(user, company, model, task):
    """ returns True if the user has the required permissions
        for the given company, model and task
        
        model is a string
        
        task can be: 'list' or 'edit' (edit includes add, edit, delete)
    """

    # get permission from memcache... 
    ckey = permission_cache_key(user, company)
    permission = cache.get(ckey)
    # ...or database
    if not permission:
        try:
            permission = Permission.objects.get(user__id=user.id, company=company)
            cache.set(ckey, permission)
        except Permission.DoesNotExist:
            # there's no entry in the database,
            # therefore the user has no permissions whatsoever
            return False
    
    if model in g.PERMISSIONS[permission.permission][task]:
        return True
    else:
        return False


def no_permission_view(request, company, action):
    """ the view that is called if user attempts to do shady business without permission """
    
    context = {
        'title': _("Permission denied"),
        'site_title': g.MISC['site_title'],
        'company': company,  # required for the 'manage' template: links need company parameter
        'action': action,
    }
    
    return render(request, 'pos/no_permission.html', context)


### deletion of objects in management
def manage_delete_object(request, company_url_name, model, messages):
    """
        a generic delete function (must be wrapped in a view)
        model: the actual model class (i.e. Discount)
        messages: a list of error messages:
           messages[0]: no permission
           message[1]: does not exist/integrity error
    """
    try:
        c = Company.objects.get(url_name=company_url_name)
    except Company.DoesNotExist:
        return JSON_error(_("Company not found"))

    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, model.__name__.lower(), 'edit'):
        return JSON_error(messages[0])

    # discount id is in request.POST in JSON format
    id = JSON_parse(request.POST.get('data')).get('id')
    if not id:
        return JSON_error(_("No id specified."))

    try:
        model.objects.get(id=id, company=c).delete()
    except (model.DoesNotExist, IntegrityError) as e:
        return JSON_error(messages[1] + "; " + e.message)

    return JSON_ok()
