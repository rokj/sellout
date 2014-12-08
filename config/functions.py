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

from config.models import UserConfig
from config.models import CompanyConfig

from common import globals as g
from django.core.cache import cache
import json


company_defaults = {
    # localization
    'pos_date_format': 'yyyy-mm-dd',  # keys for DATE_FORMATS dictionary in globals
    'pos_time_format': '23:59',  # keys for TIME_FORMATS dictionary in globals
    'pos_timezone': 'utc',  # keywords for pytz timezones
    'pos_currency': "$",
    'pos_decimal_separator': '.',
    # billing and calculation defaults
    'pos_decimal_places': 2,  # default decimal places for display
}

user_defaults = {
    'pos_product_button_size': 'medium',  # keys for PRODUCT_BUTTON_DIMENSIONS in globals
    'pos_interface_bill_width': 370,  # width of the bill area in terminal (in pixels)
    'pos_product_display': 'box',
    'pos_display_breadcrumbs': True,
}


# caching helpers
def user_cache_key(user):
    # TODO: anonymous users
    if user.is_authenticated():
        return "config_" + str(user.id)
    else:
        return "config_default"


def company_cache_key(company):
    if not company:
        return 'company_default'
    else:
        return "company_" + str(company.id)


# load config and store it to memcache
def load_user_config(user):
    try:
        c = UserConfig.objects.get(user=user)
    except UserConfig.DoesNotExist:
        # use defaults
        c = UserConfig(created_by=user,
                       user=user,
                       data=json.dumps(user_defaults))
        c.save()

    # parse json from the database (or defaults)
    return json.loads(c.data)


def load_company_config(user, company):
    try:
        c = CompanyConfig.objects.get(company=company)
    except CompanyConfig.DoesNotExist:
        # use defaults
        c = CompanyConfig(created_by=user,
                          company=company,
                          data=json.dumps(company_defaults))
        c.save()

    # parse json from the database (or defaults)
    return json.loads(c.data)


def save_user_config(user, data):
    # update or save settings
    try:
        c = UserConfig.objects.get(user=user)
        c.data = json.dumps(data)
        c.save()
    except UserConfig.DoesNotExist:
        c = UserConfig(created_by=user,
                       user=user,
                       data=json.dumps(data))
        c.save()
    
    # delete cache
    cache.delete(user_cache_key(user))


def save_company_config(user, company, data):
    # update or save settings
    try:
        c = CompanyConfig.objects.get(company=company)
        c.data = json.dumps(data)
        c.save()
    except CompanyConfig.DoesNotExist:
        c = CompanyConfig(created_by=user, company=company, data=json.dumps(data))
        c.save()

    # delete cache
    cache.delete(company_cache_key(user))


def get_user_config(user):
    """ 
        get user's config either from memcache or from database
        if user is not authenticated, return defaults
    """
    if user.is_authenticated():
        ckey = user_cache_key(user)
        data = cache.get(ckey)
        
        if not data:
            data = load_user_config(user)
            cache.set(ckey, data)
        
        return data
    else:
        return user_defaults


def get_company_config(user, company):
    """
        get user's config either from memcache or from database
        if user is not authenticated, return defaults
    """
    ckey = company_cache_key(company)
    data = cache.get(ckey)

    if not data:
        data = load_company_config(user, company)
        cache.set(ckey, data)

    return data


def get_user_value(user, key):
    data = get_user_config(user)

    # check if the value is in the dictionary
    if key in data:
        return data[key]
    else:
        # if key is in default settings, add value from defaults and save
        if key in user_defaults:
            data[key] = user_defaults[key]
            save_user_config(user, data)
            return data[key]
        else:
            raise KeyError("Invalid user config key: " + key)


def get_company_value(user, company, key):
    data = get_company_config(user, company)

    # check if the value is in the dictionary
    if key in data:
        return data[key]
    else:
        # if key is in default settings, add value from defaults and save
        if key in company_defaults:
            data[key] = company_defaults[key]
            save_company_config(user, company, data)
            return data[key]
        else:
            raise KeyError("Invalid company config key: " + key)


def set_user_value(user, key, value):
    data = get_user_config(user)

    # if it's not a boolean or an integer, convert it to string
    if not isinstance(value, bool) and not isinstance(value, int):
        value = unicode(value)

    data[key] = value
    save_user_config(user, data)  # memcache is handled in save_cofig


def set_company_value(user, company, key, value):
    data = get_company_config(user, company)

    # if it's not a boolean or an integer, convert it to string
    if not isinstance(value, bool) and not isinstance(value, int):
        value = unicode(value)

    data[key] = value
    save_company_config(user, company, data)  # memcache is handled in save_cofig


# shortcuts: date format
def get_date_format(user, company, variant):
    """ returns g.DATE_FORMATS[user's date format][variant]
        variant is one of 'python', 'django', 'jquery'
    """
    return g.DATE_FORMATS[get_company_value(user, company, 'pos_date_format')][variant]


# time format
def get_time_format(user, company, variant):
    """ returns g.TIME_FORMATS[user's date format][variant]
        variant is one of 'python', 'django', 'jquery'
    """
    return g.TIME_FORMATS[get_company_value(user, company, 'pos_time_format')][variant]

class InvalidKeyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
