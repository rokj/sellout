from django.shortcuts import render
from django.forms import ValidationError
from django.utils.translation import ugettext as _

from common import globals as g 


from django.http import HttpResponse
import json
import Image # PIL or pillow must be installed

# requests and responses
def error(request, message):
    return render(request, 'pos/error.html', {'message':message})

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
    
    if width < dimensions[0] and height < dimensions[1]:
        return # no need for resizing, image is smaller than requested
    
    image.thumbnail(dimensions, Image.ANTIALIAS)
    image.save(path)

def validate_image(obj): # obj is actually "self"
    # Kudos: stackoverflow.com/questions/6195478/max-image-size-on-file-upload
    image = obj.cleaned_data.get('image', False)
    if image:
        if image._size > g.MISC['max_upload_image_size']:
            raise ValidationError(_("Image too large, maximum file size for upload is %s MB")%(g.MISC['max_upload_image_size']/2**20))
        return image
    else:
        raise ValidationError(_("Reading of image file failed."))

    
    