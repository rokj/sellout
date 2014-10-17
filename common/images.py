from StringIO import StringIO
import ImageOps
from django.core.files.base import ContentFile
import Image
import re
from django.core.files.uploadedfile import SimpleUploadedFile

import common.globals as g


def resize_image(image, dimensions, mode='fill', color=(255, 255, 255, 0)):
    if mode == 'fill':
        # crop the image to fill the whole 'dimensions' rectangle
        return ImageOps.fit(image, dimensions, Image.ANTIALIAS)

    if mode == 'aspect':
        # resize image to fit the dimensions and keep the aspect ratio
        image.thumbnail(dimensions, Image.ANTIALIAS)

        return image

    if mode == 'fit':
        # make a border around the image and paste a resized image into it
        # kudos: http://stackoverflow.com/questions/1386352/

        # resize image to maximum dimension
        required_aspect = float(dimensions[0]) / float(dimensions[1])
        current_aspect = float(image.size[0]) / float(image.size[1])

        if current_aspect > required_aspect:
            # the current image is wider than expected, make it narrower (and shorter)
            new_width = dimensions[0]
            new_height = int(float(dimensions[0])/float(current_aspect))
        else:
            # the current image is higher than expected
            new_height = dimensions[1]
            new_width = int(current_aspect*float(dimensions[1]))

        image = image.resize((new_width, new_height), Image.ANTIALIAS)

        background = Image.new('RGBA', dimensions, color)
        background.paste(image, ((dimensions[0] - new_width) / 2, (dimensions[1] - new_height) / 2))

        return background


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

    return ContentFile(image_data, "fakename." + filetype)  # name will be replaced when saving to ImageField


def import_color_image(base64_data, dimensions, fit_mode):
    image_file = image_from_base64(base64_data)

    if not image_file:
        return None

    resize = False

    # resize and convert image if necessary
    color_logo = Image.open(image_file)

    if color_logo.mode not in ('L', 'RGB'):
        # Kudos: http://stackoverflow.com/questions/9166400/convert-rgba-png-to-rgb-with-pil
        # create a white image the same size as color_logo
        color_logo = color_logo.convert('RGBA')

        background = Image.new("RGB", color_logo.size, (255, 255, 255))
        background.paste(color_logo, mask=color_logo.split()[3])  # 3 is the alpha channel

        color_logo = background
        color_logo = color_logo.convert('RGB')

    if color_logo.size != dimensions:
        # the logo has wrong dimensions
        resize = True

    if color_logo.format != g.MISC['image_format']:
        # the logo is not in the correct format
        resize = True

    if resize:
        color_logo = resize_image(color_logo, dimensions, fit_mode)

    return color_logo


def import_monochrome_image(base64_data, dimensions, fit_mode):
    image_file = image_from_base64(base64_data)

    if not image_file:
        return None

    resize = False

    # resize and convert image if necessary
    monochrome_logo = Image.open(image_file)

    if monochrome_logo.size != g.IMAGE_DIMENSIONS['monochrome_logo']:
        # the logo has wrong dimensions
        resize = True

    if monochrome_logo.format != g.MISC['image_format']:
        # the logo is not in the correct format
        resize = True

    # resize first
    if resize:
        monochrome_logo = resize_image(monochrome_logo, dimensions, fit_mode)

    # then convert to monochrome
    if monochrome_logo.mode != '1':
        monochrome_logo = monochrome_logo.convert('1')

    return monochrome_logo


def create_file_from_image(image):
    temp_handle = StringIO()

    image.save(temp_handle, g.MISC['image_format'])
    temp_handle.seek(0)

    # Save to the thumbnail field
    suf = SimpleUploadedFile('temp', temp_handle.read(), ('image/' + g.MISC['image_format']).lower())

    return {'file': suf, 'name': suf.name + '.' + g.MISC['image_format']}