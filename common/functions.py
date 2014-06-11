from django.db import connection
import string
from random import choice
import globals as g

def get_random_string(length=8, chars=string.letters + string.digits):
    return ''.join([choice(chars) for _ in xrange(length)])


def get_image_path(path, table_name):
    """ returns a random name for a newly uploaded image 
    takes care of the birthday problem """
    def upload_callback(instance, filename):
        if not filename or len(filename) == 0:
            filename = instance.image.name
        cursor = connection.cursor()

        # image extension (format)
        #ext = os.path.splitext(filename)[1] # for preserving the original format
        #ext = ext.lower()
        ext = '.' + g.MISC['image_format'].lower() # to apply a fixed default

        random_filename = get_random_string(length=16)
        row = True
        while row:
            cursor.execute('SELECT id FROM ' + table_name + ' WHERE image = %s', [random_filename])
            if cursor.fetchone():
                row = True
                random_filename = get_random_string(length=8)
            else:
                row = False

        # instance.original_filename = filename
        return '%s/%s' % (path, random_filename + ext)

    return upload_callback


def get_terminal_url(request):
# future store url: same as this page's, excluding what's after the
    # g.MISC['management_url'] string
    # blocklogic.net/pos/app/register-company >> blocklogic.net/pos/company-name
    full_url = request.build_absolute_uri()
    return full_url[:full_url.rfind(g.MISC['management_url'] + '/')]
