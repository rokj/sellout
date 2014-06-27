from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files import File
from django.utils.translation import ugettext as _

import Image
import re
import os

import common.globals as g


def resize_image(image, dimensions):
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