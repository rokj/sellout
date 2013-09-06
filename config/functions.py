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
    'pos_default_tax':0.0,
}
    
# caching helpers
def cache_key(user):
    return "config_" + str(user.id)

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
    """ get user's config either from memcache or from database """
    ckey = cache_key(user)
    data = cache.get(ckey)
    
    if not data:
        data = load_config(user)
        cache.set(ckey, data)

    return data

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
            return data[key]
        else:
            return "<invalid key: '" + "':'" + key + "'>"

# shortcuts: date
def get_date_format(user, variant):
    """ returns g.DATE_FORMATS[user's date format][variant] """
    return g.DATE_FORMATS[get_value(user, 'pos_date_format')][variant]

def set_value(user, key, value):
    data = get_config(user)
    data[key] = value
    save_config(user) # memcache is handled in save_cofig
