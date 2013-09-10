from django.shortcuts import render
from django.forms import ValidationError
from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.http import HttpResponse

from common import globals as g
from pos.models import Permission

import json
import Image # PIL or pillow must be installed

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
    return json.loads(string_data)

# image and file handling
def resize_image(path, dimensions):
    image = Image.open(path)
    
    width, height = image.size
    
    if width <= dimensions[0] and height <= dimensions[1]:
        return # no need for resizing, image is smaller than requested
    
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

# number output: show only non-zero decimal places
def format_number(n):
    """ returns string with decimal number n,
        without trailing or leading zeros
    """
    # strip zeros and if there was no decimal places, also strip the dot
    return str(n).strip('0').strip('.')
    
# permissions: cached
def permission_cache_key(user, company):
        return "permission_" + str(user.id) + "_" + str(company.id)

def has_permission(user, company, required_level):
    """ returns True if the user has the required permissions for the given company
        and False otherwise """
        
    ckey = permission_cache_key(user, company)
    permission = cache.get(ckey)
    
    if not permission:
        try:
            permission = Permission.objects.get(user__id=user.id)
            cache.set(ckey, permission)
        except Permission.DoesNotExist:
            # no, user hasn't got it
            return False
     
    if permission.permission >= required_level:
        return True
    else:
        return False

def no_permission_view(request, company, action):
    """ the view that is called if user attempts to do shady business without permission """
    
    context = {
        'title':_("Company details"),
        'site_title':g.MISC['site_title'],
        'company':company, # required for the 'manage' template: links need company parameter
        'action':action,
    }
    
    return render(request, 'pos/manage/no_permission.html', context)