import json
from decimal import Decimal
from datetime import datetime
from xdg.Exceptions import ValidationError

from django.db.backends.dummy.base import IntegrityError
from django import forms
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.http import JsonResponse
from django.forms.models import model_to_dict

from common import globals as g
from config.functions import get_date_format, get_time_format, get_company_value
from pos.models import Permission, Company
from common.models import SkeletonU


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


def JsonStringify(data):
    # the data will be put into template with |safe filter or
    # within {% autoescape off %},
    # so make sure there's no harmful stuff inside
    s = json.dumps(data)
    s = s.replace('<', '\u003c')
    s = s.replace('>', '\u003e')
    s = s.replace('&', '\u0026')

    return s


def JsonError(message):
    return JsonResponse({'status': 'error', 'message': message})


def JsonOk(extra=None):
    data = {'status': 'ok'}
    if extra:
        data['data'] = extra

    return JsonResponse(data)


def JsonParse(string_data):
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
        s = str(n.quantize(Decimal('1.'+'0'*p*2)))  # for calculation, use more decimal places
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
        
        task can be: 'view' or 'edit' (edit includes add, edit, delete)
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
        return JsonError(_("Company not found"))

    # check permissions: needs to be at least manager
    if not has_permission(request.user, c, model.__name__.lower(), 'edit'):
        return JsonError(messages[0])

    # discount id is in request.POST in JSON format
    id = JsonParse(request.POST.get('data')).get('id')
    if not id:
        return JsonError(_("No id specified."))

    try:
        model.objects.get(id=id, company=c).delete()
    except (model.DoesNotExist, IntegrityError) as e:
        return JsonError(messages[1] + "; " + e.message)

    return JsonOk()


###
### stuff for working on similar models
###
# (like Contact - BillContact: almost all fields on both models are inherited from ContactAbstract)
def get_common_keys(dict1, dict2):
    """ returns a list common keys in two dictionaries """
    return list(set(dict1.keys()) & set(dict2.keys()))


def remove_skeleton_fields(fields):
    """
        exclude names of all fields from SkeletonU: created_by, updated_by, timestamps etc...
        but no hardcoding, Mr. Beaufort!
    """
    skeleton_fields = SkeletonU._meta.get_all_field_names() + ['id']  # id must be assigned by database

    for field in skeleton_fields:
        if field in fields:
            fields.remove(field)

    return fields


def compare_objects(obj1, obj2):
    """
        comparation of two different models with the same data
        (used for checking if Company has changed so that it needs a new BillCompany entry)
        (applies to other models as well - BillContact, BillRegister)
    """
    d1 = model_to_dict(obj1)
    d2 = model_to_dict(obj2)

    common_fields = remove_skeleton_fields(get_common_keys(d1, d2))

    # if any of the fields mismatch, the models are not equal.
    for key in common_fields:
        if d1[key] != d2[key]:
            return False

    # the models are equal.
    return True


def copy_data(from_obj, to_obj):
    """
        copy data from fields in obj1 to fields in obj2.
        only do this for fields that are on both objects;
        those are fields from the same abstract
    """
    from_d = from_obj.__dict__
    to_d = to_obj.__dict__

    common_fields = remove_skeleton_fields(get_common_keys(from_d, to_d))

    # copy all common fields' values from obj1 to obj2
    for field in common_fields:
        to_d[field] = from_d[field]


# custom forms and fields...
class CompanyUserForm(forms.Form):
    def __init__(self, user=None, company=None, *args, **kwargs):
        super(CompanyUserForm, self).__init__(*args, **kwargs)

        assert user
        assert company

        self.user = user
        self.company = company

        # set user and company to all fields in this form
        for f in getattr(self, 'fields', None):
            self.fields[f].user = self.user
            self.fields[f].company = self.company


class CustomDateField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(CustomDateField, self).__init__(*args, **kwargs)

        # these will be set by CompanyUserForm;
        self.user = None
        self.company = None

    def clean(self, date):
        if not date:
            return None

        assert self.user is not None
        assert self.company is not None

        r = parse_date(self.user, self.company, date)
        if not r['success']:
            raise ValidationError(_("Invalid date format"), None)
        else:
            return r['date']


class CustomDecimalField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(CustomDecimalField, self).__init__(*args, **kwargs)

        # these will be set by CompanyUserForm;
        self.user = None
        self.company = None

    def clean(self, number):
        if not number:
            return None

        assert self.user is not None
        assert self.company is not None

        r = parse_decimal(self.user, self.company, number)
        if not r['success']:
            raise ValidationError(_("Invalid number format"), None)
        else:
            return r['number']