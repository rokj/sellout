from django.shortcuts import render
from django.forms import ValidationError
from django.utils.translation import ugettext as _

from common import globals as g 


from django.http import HttpResponse
import json
import Image # PIL or pillow must be installed
import re

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