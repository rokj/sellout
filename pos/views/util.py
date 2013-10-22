from django.shortcuts import render
from django.forms import ValidationError
from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.http import HttpResponse
from django.core.files.base import ContentFile

from common import globals as g
from config.functions import get_date_format, get_time_format, get_value
from pos.models import Permission

import json
import Image # PIL or pillow must be installed
import re
from decimal import Decimal
from datetime import datetime

# requests and responses
def error(request, message):
    
    context = {'message':message,
               'back_link':request.build_absolute_uri(),
               }
    return render(request, 'pos/error.html', context)

def JSON_stringify(data):
    return json.dumps(data)
    
def JSON_response(data):
    return HttpResponse(JSON_stringify(data), mimetype="application/json")

def JSON_error(message):
    return JSON_response({'status':'error', 'message':message})

def JSON_ok():
    return JSON_response({'status':'ok'})

def JSON_parse(string_data):
    try:
        return json.loads(string_data)
    except:
        return None
        
# misc
def max_field_length(model, field_name):
    return model._meta.get_field(field_name).max_length

# image and file handling
def resize_image(path, dimensions):
    image = Image.open(path)
    # always "resize" - convert image to maintain consistent format for all uploads
    # width, height = image.size
    # if width <= dimensions[0] and height <= dimensions[1]:
    #     return # no need for resizing, image is smaller than requested
    # also resize to un-animate any animated GIFs
    image.thumbnail(dimensions, Image.ANTIALIAS)
    image.save(path, g.MISC['image_format'])

def validate_image(obj): # obj is actually "self"
    image = obj.cleaned_data.get('image', False)
    
    # possible cases:
    # 1. a new upload: image object will contain all data, including _size etc.; check for size
    # 2. deletion: image = False; do nothing
    # 3. no change: image object will exist, but image._size will not; do nothing    
    try:
        if image._size > g.MISC['max_upload_image_size']:
            raise ValidationError(_("Image too large, maximum file size for upload is %s MB")%(g.MISC['max_upload_image_size']/2**20))
    except AttributeError: # case 3
        pass
    
    return image

def image_dimensions(size):
    """ accepts string - key in g.IMAGE_DIMENSIONS and returns
        a list: [width, height, sorl_string]
        sorl_string = <width>x<height> (for use in templates)
    """
    if size not in g.IMAGE_DIMENSIONS:
        return None # an exception will be raised on access
    
    dim = g.IMAGE_DIMENSIONS[size]
    
    return [dim[0], dim[1], str(dim[0]) + "x" + str(dim[1])]

def image_from_base64(data):
    """ receives base64 data and returns a file for saving to ImageField """
    # see if header is right (if it's not at the beginning of data, it' not there at all
    m = re.search(r"^data:image\/(" + g.MISC['image_upload_formats'] + ");base64,", data[:30])
    if not m:
        return None
    header = m.group(0)
    
    # get file type from header
    start = header.index("data:image/") + len("data:image/") # search between these substrings
    end = header.index(";base64,", start)
    filetype = header[start:end]

    image_data = data[len(header)-1:].decode("base64")

    return ContentFile(image_data, "fakename." + filetype) # name will be replaced when saving to ImageField

# numbers
def format_number(user, n, high_precision=False):
    """ returns formatted decimal number n;
        strips zeros, but leaves <p> numbers after decimal point even if they are zero
    """
    sep = get_value(user, 'pos_decimal_separator')
    p = int(get_value(user, 'pos_decimal_places'))
    
    if not n:
        return '0'
    
    if high_precision:
        s = str(n.quantize(Decimal('1.'+'0'*p*2)))
    else:
        s = str(n.quantize(Decimal('1.'+'0'*p)))
    
    return s.replace('.', sep)
        
def format_date(user, date, send_to='python'):
    """ formats date for display according to user's settings """
    if not date:
        return ''
    else:
        return date.strftime(get_date_format(user, send_to))

def format_time(user, date):
    """ formats time for display according to user's settings """
    if not date:
        return ''
    else:
        return date.strftime(get_time_format(user, 'python'))

def parse_decimal(user, string, max_digits=None):
    """ replace user's decimal separator with dot and parse
        return dictionary with result status and parsed number:
        
        {'success':True/False, number:<num>/None}
    """
    
    if user: # if user is None, try with the dot (user should never be None - 
             # this is to avoid checking on every function call)
        string = string.replace(get_value(user, 'pos_decimal_separator'), '.')
    
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

def parse_date(user, string):
    """ parses date in string according to user selected preferences
        return dictionary with result status and parsed datetime:
        
        {'success':True/False, date:<num>/None}
    """
    try:
        d = datetime.strptime(string, get_date_format(user, 'python'))
    except:
        return {'success':False, 'date':None}
   
    return {'success':True, 'date':d}

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
        'title':_("Permission denied"),
        'site_title':g.MISC['site_title'],
        'company':company, # required for the 'manage' template: links need company parameter
        'action':action,
    }
    
    return render(request, 'pos/no_permission.html', context)
