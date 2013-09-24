# coding=UTF-8

# 2013-09-04, nejc
# config's settings manipulation:
"""
  Config:
  all settings for a specified user are stored in json format:
    app1_s1:val1
    app1_s2:val2
      ...
    app2_s1:val3
    app2_s2:val4
      ...
  and memcached:
    cache key: config_<user id>
  cache is loaded on load_config and deleted on save_config (and reloaded)
"""

from models import Config
from common import globals as g
from django.core.cache import cache
import json

defaults = {
    'pos_date_format':'yyyy-mm-dd', # keys for DATE_FORMATS dictionary in globals
    'pos_timezone':'utc', # keywords for pytz timezones
    'pos_currency':"$",
    'pos_contacts_per_page':10,
    'pos_discounts_per_page':10,
    'pos_default_tax':'0.0',
    'pos_decimal_separator':'.',
    'pos_interface':'keyboard', # options: 
}
    
# caching helpers
def cache_key(user):
    # TODO: anonymous users
    if user.is_authenticated():
        return "config_" + str(user.id)
    else:
        return "config_default"

def load_config(user):
    try:
        c = Config.objects.get(user=user)
    except Config.DoesNotExist:
        # use defaults
        c = Config(created_by = user,
            user = user,
            data = json.dumps(defaults))
        c.save()

    # parse json from the database (or defaults)
    return json.loads(c.data)

def save_config(user, data):
    # update or save settings
    try:
        c = Config.objects.get(user=user)
        c.data = json.dumps(data)
        c.save()
    except Config.DoesNotExist:
        c = Config(created_by = user,
            user = user,
            data = json.dumps(data))
        c.save()
    
    # delete cache
    cache.delete(cache_key(user))
    
def get_config(user):
    """ 
        get user's config either from memcache or from database
        if user is not authenticated, return defaults
    """
    if user.is_authenticated():
        ckey = cache_key(user)
        data = cache.get(ckey)
        
        if not data:
            data = load_config(user)
            cache.set(ckey, data)
        
        return data
    else:
        return defaults

def get_value(user, key):
    data = get_config(user)

    # check if the value is in the dictionary
    if key in data:
        return data[key]
    else:
        # if key is in default settings, add value from defaults and save
        if key in defaults:
            data[key] = defaults[key]
            save_config(user, data)
            print data[key]
            return data[key]
        else:
            return "<invalid key: '" + "':'" + key + "'>"

def set_value(user, key, value):
    data = get_config(user)
    data[key] = value
    save_config(user, data) # memcache is handled in save_cofig

# shortcuts: date format
def get_date_format(user, variant):
    """ returns g.DATE_FORMATS[user's date format][variant]
        variant is one of 'python', 'django', 'jquery'
    """
    return g.DATE_FORMATS[get_value(user, 'pos_date_format')][variant]