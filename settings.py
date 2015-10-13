# Django settings for webpos project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'pos',                      # Or path to database file if using sqlite3.
        'USER': 'pos',                      # Not used with sqlite3.
        'PASSWORD': 'pos',            # Not used with sqlite3.
        'HOST': 'localhost',                # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                     # Set to empty string for default. Not used with sqlite3.
    },
    'bl_mail': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
    'bl_users': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'users',                      # Or path to database file if using sqlite3.
        'USER': 'users',                      # Not used with sqlite3.
        'PASSWORD': 'users',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
    },
    'bitcoin': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
}

SITE_URL = ''

PROJECT_ID = 'pos' # used for users db

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Ljubljana'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'si'      # when adding a language,
LANGUAGES = ('en', 'si')  # add its alphabet to common/globals

LOCALE_PATHS = (
    '/home/rokj/development/django/webpos/locale',
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

STATIC_DIR = ''

LOGIN_URL = '/#login'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    STATIC_DIR,
    os.path.join(os.path.dirname(__file__), 'static').replace('\\', '/'),
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# session: we're using memcached, so use memcached-based sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'blusers',
    'captcha',
    'config',
    'pos',
    'sorl.thumbnail',
    'rest_framework',
    'rest_framework.authtoken',
    'mobile',
    'sync',
    'web',
    'action',
    'payment',
    'support',
    'registry',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'webpos.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'webpos.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), 'templates').replace('\\', '/'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (),
    'PAGINATE_BY': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    )
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/sellout_debug.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
        }
    }
}

# sorl-thumbnail config
THUMBNAIL_DEBUG = True
THUMBNAIL_FORMAT = "PNG"
THUMBNAIL_KEY_PREFIX = "sorl_"

GOOGLE_API = {
    'client_id': '',
    'client_secret': '',
    'client_userinfo': ''
}

FONTS_DIR = STATIC_DIR + "/fonts/"

AUTHENTICATION_BACKENDS = ('bl_auth.BlocklogicMailAuthBackend', )
AUTHENTICATION_BACKENDS = (
    'social_auth.backends.google.GoogleOAuth2Backend',
    'bl_auth.BlocklogicMailAuthBackend'
    # 'django.contrib.auth.backends.ModelBackend',
)


AUTH_USER_MODEL = 'blusers.BlocklogicUser'

USED_BLUSER_BACKENDS = ('bluser',)

EMAIL_FROM = 'info@sellout.biz'
EMAIL_SUBJECT_PREFIX = ''

# captcha settings
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'
CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_dots',)
CAPTCHA_FONT_SIZE = 30
CAPTCHA_LETTER_ROTATION = (-10, 10)

# keys should be same as in globals
PAYMENT = {
    'bitcoin' : {
        'rpcuser': '',  # you'll find these settings in your $HOME/.bitcoin/bitcoin.conf
        'rpcpassword': '',
        'host': '',
        'port': '',
        'account': '',
        'minconf': 1,
        'account_prefix': 'sellout_',
        'walletpassphrase': '',
        'walletpassphrase_timeout': 10,
        'minimum_keypoolsize': 98
    },
    'paypal': {
        'client_id': '',
        'secret': '',
        'url': '',
        'host_for_return_url': '',
        'host_for_cancel_url': '',
        'sandbox_ipn_endpoint': 'https://www.sandbox.paypal.com/cgi-bin/webscr',
        'live_ipn_endpoint': 'https://www.paypal.com/cgi-bin/webscr'
    },
    'free': {},
    'cash': {},
    'credit_card': {}
}

PAYMENT_OFFICER = {
    "bitcoin_check_interval": "",
    "sepa_check_interval": "",
    "bitcoin_payment_waiting_interval": "",  # in hours
    "sepa_payment_waiting_interval": "",  # in days
    "bitcoin_db": {
        'hostname': '',
        'username': '',
        'password': '',
        'database': ''
    },
    "btc_exchange": {
        "USD": "bitstamp",
        "EUR": "bitstamp"
    }
}

BTC_PRICE = "/tmp/btc_prices.txt"
MAX_BTC_PRICE_UPDATE_INTERVAL = 60  # in minutes

CONTACT_EMAIL = ''
SUPPORT_EMAIL = ''

# TESTS = ['calculate_btc_price', 'btc_address', 'create_user', 'create_company']
TESTS = ['create_user', 'create_company']

try:
    if os.environ['DJANGO_SETTINGS_MODULE'] == 'sellout_biz.spletna_blagajna_settings':
        print "spletna-blagajna.si settings loading"
        print
        from spletna_blagajna_settings import *
    else:
        print "sellout.biz settings loading"
        print
        from settings_local import *
except:
    print "Local settings not found"