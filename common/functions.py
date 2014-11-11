import os
import string
from random import choice
from django.core.urlresolvers import reverse
from django.db import connection
from django.shortcuts import redirect
import globals as g
import settings


def get_random_string(length=8, chars=string.letters + string.digits):
    return ''.join([choice(chars) for _ in xrange(length)])


def get_terminal_url(request):
# future store url: same as this page's, excluding what's after the
    # g.MISC['management_url'] string
    # blocklogic.net/pos/app/register-company >> blocklogic.net/pos/company-name
    full_url = request.build_absolute_uri()
    return full_url[:full_url.rfind(g.MISC['management_url'] + '/')]

def redirect_to_selected_company(user, ajax=False):
    selected_company = user.selected_company

    if selected_company == "":
        return redirect('index')

    # if ajax:
        # return reverse('web:home', kwargs={'group_id': group.id, 'section': 'home'})

    return redirect('index')

DEFAULT_IMAGE_PATH = "images/omg"
def get_image_path(path, table_name):
    """
    DEFAULT_IMAGE_PATH should happen once in a life time. You better know why.
    """
    def upload_callback(instance, filename):
        if not filename or len(filename) == 0:
            filename = instance.image.name
        cursor = connection.cursor()

        ext = os.path.splitext(filename)[1]
        ext = ext.lower()

        random_filename = get_random_string(length=8)
        tries = 0
        while tries < 3:
            cursor.execute('SELECT * FROM ' + table_name + ' WHERE image = %s', [random_filename])
            row = cursor.fetchone()
            if row:
                tries += 1
                random_filename = get_random_string(length=8)
            else:
                break

        if tries == 3:
            return DEFAULT_IMAGE_PATH

        # instance.original_filename = filename
        return '%s/%s' % (path, random_filename + ext)

    return upload_callback

def redirect_to_subscriptions(ajax=False):
    if ajax:
        return reverse('subscription:new')

    return redirect('subscription:new')

def site_title():
    return settings.GLOBAL['site_title']