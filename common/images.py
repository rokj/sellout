from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files import File
from django.utils.translation import ugettext as _

import Image
import re
import os

import common.globals as g

def resize_image(path, dimensions):
    image = Image.open(path)

    # crop the image to make it square
    w = image.size[0]
    h = image.size[1]

    dim = min([w, h])

    if w > h:
        # the image is landscape, crop left and right
        dist = (w - dim)/2
        box = (dist, 0, w-dist, h)
    else:
        # the image is portrait, crop up and down
        dist = (h - dim)/2
        box = (0, dist, w, h-dist)

    image = image.crop(box)

    # create a thumbnail of the cropped image
    image.thumbnail(dimensions, Image.ANTIALIAS)

    # strip extension from path and use custom (so the file will be converted to our format)
    path = os.path.splitext(path)[0]

    image.save(path + '.' + g.MISC['image_format'])


def color_to_monochrome_logo(c):  # c  a.k.a. Company
    # create a monochrome logo and save it

    # check if the company already has a logo
    if not c.color_logo:
        return False

    # get company's color logo
    color_logo = Image.open(c.color_logo.path)
    # resize it to monochrome_logo dimension
    black_logo = color_logo.copy()
    black_logo.thumbnail(g.IMAGE_DIMENSIONS['monochrome_logo'], Image.ANTIALIAS)
    # reduce color depth
    black_logo = black_logo.convert(mode='1')
    # create a new path for the monochrome logo
    new_path = os.path.splitext(c.color_logo.path)[0]
    new_path = new_path + '_monochrome.' + g.MISC['image_format']
    # save to the new path
    black_logo.save(new_path, g.MISC['image_format'], bits=1)

    # save to stupid django field
    django_file = File(open(new_path))
    c.monochrome_logo.save('new', django_file)
    django_file.close()

    return True


def validate_image(obj): # obj is actually "self"
    image = obj.cleaned_data.get('image', False)

    # possible cases:
    # 1. a new upload: image object will contain all data, including _size etc.; check for size
    # 2. deletion: image = False; do nothing
    # 3. no change: image object will exist, but image._size will not; do nothing
    try:
        if image._size > g.MISC['max_upload_image_size']:
            raise ValidationError(_("Image too large, maximum file size for upload is %s MB")%(g.MISC['max_upload_image_size']/2**20))
    except AttributeError:  # case 3
        pass

    return image


def resize_logos(company):
    # check if both of company's logos are of the right size and shape, and if not,
    # convert to what we need

    replace_color = False
    replace_monochrome = False

    # color logo: format must be png of size g.IMAGE_DIMENSIONS['color_logo']
    if company.color_logo:
        with open(str(company.color_logo.path), 'rb') as i:
            color_logo = Image.open(i)

            if color_logo.size != g.IMAGE_DIMENSIONS['color_logo']:
                # the logo has wrong dimensions
                replace_color = True

            if color_logo.format != g.MISC['image_format']:
                # the logo is not in the correct format
                replace_color = True

        if replace_color:
            resize_image(company.color_logo.path, g.IMAGE_DIMENSIONS['color_logo'])

    # monochrome logo: it must be a 1-bit png of size g.IMAGE_DIMENSIONS['monochrome_logo']
    if company.monochrome_logo:
        with open(str(company.monochrome_logo.path), 'rb') as i:
            monochrome_logo = Image.open(i)

            if monochrome_logo.size != g.IMAGE_DIMENSIONS['monochrome_logo']:
                # the logo is of the wrong size
                replace_monochrome = True

            if monochrome_logo.mode != '1':
                # the logo is not monochrome
                replace_monochrome = True

            if monochrome_logo.format != g.MISC['image_format']:
                # image is in the wrong format
                replace_monochrome = True

        if replace_monochrome:
            color_to_monochrome_logo(company)


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