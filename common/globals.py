# coding=UTF-8
from django.utils.translation import ugettext as _, ugettext

# Common stuff to be used anywhere throughout the site
import settings

if settings.LANGUAGE_CODE == "en":
    SITE_TITLE = "Sellout"
elif settings.LANGUAGE_CODE == "si":
    SITE_TITLE = "spletna-blagajna.si"

# directories
DIRS = {  # all go to MEDIA folder
    'color_logo_dir': "img/color_logo",
    'monochrome_logo_dir': "img/monochrome_logo",
    'category_icon_dir': "img/category",
    'product_icon_dir': "img/product",
    'product_image_dir': "img/product",
    'users_image_dir': "img/blusers",
    'temp': "/tmp",
}

# attributes' field lengths
ATTR_LEN = {
    'name': 30,
    'value': 100,
}

# number of digits for decimal database field
DECIMAL = {
    'currency_digits': 24,  # number of digits for money values (big money) (INCLUDING DECIMAL PLACES)
    'currency_decimal_places': 8,  # number of decimal places for money values
    'percentage_decimal_places': 8,  # number of decimal places for percentage values
    'quantity_digits': 24,
    'quantity_decimal_places': 8,
}

# unit types
# unicode superscripts: ² ³ (replacing ^* with <sup>*</sup> does not work for <select>)
UNITS = (
    ("Piece", _("Piece")),  # the first is the default
    ("g", "g"),
    ("dag", "dag"),
    ("kg", "kg"),
    ("t", "ton"),
    ("oz", "oz"),
    ("lb", "lb"),
    ("cm", "cm"),
    ("m", "m"),
    ("in", "in"),
    ("ft", "ft"),
    ("yd", "yd"),
    ("in^2", "in²"),
    ("m^2", "m²"),
    ("ft^2", "ft²"),
    ("l", "l"),
    ("dl", "dl"),
    ("cl", "cl"),
    ("m^3", "m³"),
    ("fl. oz.", "fl. oz."),
    ("pint", "pint"),
    ("gal", "gal"),
    ("ft^3", "ft³"),
    ("h", _("Hour")),
    ("other", _("Other")),
)
UNIT_CODES = [x[0] for x in UNITS]

# products
SEARCH_RESULTS = {
    'products': 200,  # return max 100 products from search
}


# discounts
DISCOUNT_TYPES = (
    ("Relative", _("Percentage")),
    ("Absolute", _("Absolute value")),
)

# contacts
CONTACT_TYPES = (
    ("Individual", _("Individual")),
    ("Company", _("Company")),
    ("None", _("None"))  # used when saving bill that has no contact selected
)

SEXES = (
    ("M", _("Male")),
    ("F", _("Female")),
    ("U", _("Undisclosed")),
)

RECEIPT_FORMATS = (
    ("Page", _("Full page (Letter/A4)")),
    ("Thermal", _("Thermal (80mm)")),
)

RECEIPT_TYPES = (
    ("Print", _("Printed")),
    ("E-mail", _("E-mail")),
)

# should be same as in settings
BITCOIN = "bitcoin"
PAYPAL = "paypal"
CASH = "cash"
CREDIT_CARD = "credit_card"

PAYMENT_TYPES = (
    (CASH, _("Cash")),  # the keys should match javascript payment types (see payment.js)
    (CREDIT_CARD, _("Credit card")),
    (BITCOIN, _("Bitcoin")),
    (PAYPAL, _("Paypal")),
)

PAYMENT_TYPE_VALUES = tuple([x[0] for x in PAYMENT_TYPES])

PRINTER_DRIVERS = (
    ("System", _("Default system printer")),
    ("Sellout", _("Sellout serial (must be installed)")),

)

# date formats
# specify all formats for each date:
#  - regular expression for checking format
#  - python's strftime format
#  - django templates
#  - jquery format string (for datepicker etc.)
DATE_FORMATS = {
    'yyyy-mm-dd': {'regex': "^\d{4}\.\d{2}\.\d{2}$",  # strictly with leading zeros
                   'python': "%Y-%m-%d",
                   'django': "Y-m-d",
                   'android': "%Y-%m-%d",
                   'js': "yy-mm-dd",
                   },
    'dd.mm.yyyy': {'regex': "^\d{1,2}\.\d{1,2}\.\d{4}$",  # with or without leading zeros
                   'python': "%d.%m.%Y",  # the docs say zero-padded decimal, but will also parse non-padded numbers
                   'django': "j.n.Y",  # show no leading zeros in template
                   'android': "%d.%m.%Y",
                   'js': "dd.mm.yy",
                   },
    'mm/dd/yyyy': {'regex': "^\d{1,2}\.\d{1,2}\.\d{4}$",  # with or without leading zeros
                   'python': "%m/%d/%Y",
                   'django': "n/j/Y",
                   'android': "%m/%d/%Y",
                   'js': "mm/dd/yy",
                  },
}

TIME_FORMATS = {
    '23:59': {  # 24-hour clock
             'regex': "^[0-2][0-4]:[0-5][0-9]$",
             'python': "%H:%M",
             'django': "H:i",
             'android': "hh:mm",
             'js': "hh:mm",  # jquery has nothing to do with time, so it will have to be formatted using javascript
            },
    '23:59:59': {  # 24-hour clock with seconds
            'regex': "^[0-2][0-4]:[0-5][0-9]:[0-5][0-9]$",
            'python': "%H:%M:%S",
            'django': "H:i:s",
            'android': "hh:mm:ss",
            'js': "hh:mm:ss",
            },
    '11:59 AM/PM': {  # 12-hour clock with AM/PM
            'regex': "^[0-2][0-4]:[0-5][0-9] (AM|PM)$",
            'python': "%I:%M %p",
            'django': "",
            'android': "",
            'js': "hh:mm AMPM",
            },
    '11:59:59 AM/PM': {  # 12-hour clock with AM/PM
             'regex': "^[0-2][0-4]:[0-5][0-9]:[0-5][0-9] (AM|PM)$",
             'python': "%r",
             'django': "",
             'android': "",
             'js': "hh:mm:ss AMPM",
            },
}

ALPHABETS = {
    'en': 'abcdefghijklmnopqrstuvwxyz',
    'si': 'abcčdefghijklmnoprsštuvzž',
}

PIN_LENGTH = 4

DATE = {
    'max_date_length': 10,
}

# misc
MISC = {
    'company_url_length': 50,
    'management_url': 'admin',  # must not be empty!
                                # (to differentiate between company and management sites)
    'max_upload_image_size': 20*2**20,  # 2 megabytes
    'image_format': 'png',  # all images will be saved in this format
    'image_upload_formats': 'jpg|jpeg|gif|png|bmp|tiff',  # supported image formats (as regex "options")
    'discounts_per_page': 12,
    'bills_per_page': 25,
    'documents_per_page': 5
}

if settings.LANGUAGE_CODE == "en":
    MISC['site_title'] = "Sellout"
elif settings.LANGUAGE_CODE == "si":
    MISC['site_title'] = "spletna-blagajna.si"

IMAGE_DIMENSIONS = {
    'color_logo': (180, 180),
    'monochrome_logo': (180, 64),
    'category': (120, 120),  # there's no image, just a colored box
    'product': (160, 160),  # must be as large as the largest PRODUCT_BUTTON_DIMENSIONS
    'thumb_small': (32, 32),  # for thumbnails
    'thumb_large': (125, 128),
}

# premissions
PERMISSION_GROUPS = (  # retrieve readable format with get_permission_display()
    ('guest',   _("Guest")),    # can only view stuff (this must be the first in the list as it's the default in error case)
    ('cashier', _("Cashier")),  # can write and edit bills
    ('seller',  _("Seller")),   # can add and edit products
    ('manager', _("Manager")),  # can add and edit discounts, contacts, categories, ...
    ('admin',   _("Admin")),    # can do anything
)

# for checking if permission in PERMISSION_TYPES
PERMISSION_TYPES = [x[0] for x in PERMISSION_GROUPS]

PERMISSIONS = {
    'disabled': {
        'view': (),
        'edit': (),
        },
    'cashier': {
        'view': ('company', 'category', 'discount', 'product', 'contact', 'bill', 'tax', 'terminal', 'register','stats', 'stock', 'document', ),
        'edit': ('bill', 'terminal', 'contact'),  # cashiers must write bills
        },
    'seller': {
        'view': ('company', 'category', 'discount', 'product', 'contact', 'bill', 'tax', 'terminal', 'manage', 'register','stats', 'stock',),
        'edit': ('bill', 'product', 'terminal', 'manage', 'contact', 'stock', 'document', ),
        },
    'manager': {
        'view': ('company', 'category', 'discount', 'product', 'contact', 'bill', 'config', 'tax', 'terminal', 'manage', 'register', 'stats', 'stock', 'document', ),
        'edit': ('category', 'discount', 'product', 'contact', 'bill', 'tax', 'terminal', 'manage', 'register', 'stock', 'document', ),
        },
    'admin': {
        'view': ('company', 'category', 'discount', 'product', 'contact', 'bill', 'config', 'terminal', 'manage', 'tax', 'register', 'user', 'stats', 'stock', 'document', ),
        'edit': ('company', 'category', 'discount', 'product', 'contact', 'bill', 'config', 'terminal', 'manage', 'tax', 'register', 'user', 'stats', 'stock', 'document', ),
        },
}

PRODUCT_BUTTON_DIMENSIONS = {
    'small': 90,  # all squares
    'medium': 125,
    'large': 160  # check IMAGE_DIMENSIONS['product']
}

CATEGORY_COLORS = [  # choices for category.color
    'ffffff',  # the first entry is the default
    '444444',
    'ff7d64',
    '00dcb4',
    '143264',
    'ff465a',
    '1ee65a',
    '8287a5',
    'b9aa9b',
    '007dff',
    'ffc864',
    '5ad2fa',
]

NO_CATEGORY_NAME = _("[No Category]")

###
### actions
###
ACTION_ACCEPTED = "accepted"
ACTION_DECLINED = "declined"
ACTION_WAITING = "waiting"
ACTION_CANCELED = "canceled"
ACTION_SEEN = "seen"

ACTION_STATUS_CHOICES = (
    ((ACTION_ACCEPTED), _("Accepted")),
    ((ACTION_DECLINED), _("Declined")),
    ((ACTION_WAITING), _("Waiting")),
    ((ACTION_CANCELED), _("Canceled")),
    ((ACTION_SEEN), _("Seen")),
)
ACTION_STATUSES = (x[0] for x in ACTION_STATUS_CHOICES)


ACTION_INVITATION = "invitation"
ACTION_NOTIFICATION = "notification"

ACTION_TYPE_CHOICES = (
    ((ACTION_INVITATION), _("Invite")),
    ((ACTION_NOTIFICATION), _("Notification")),
)
ACTION_TYPES = (x[0] for x in ACTION_TYPE_CHOICES)


###
### logins and subscriptions
###
BL_USERS = "bl_users"
BL_MAIL = "bl_mail"
NORMAL = "normal"
GOOGLE = "google"

LOGIN_TYPES = (
    (BL_USERS, _("Master BL users table")),
    (BL_MAIL, _("Blocklogic mail")),
    (NORMAL, _("Normal")),
    (GOOGLE, _("Google"))
)

FIRST_TIME = "first_time"
PAID = "paid"
FREE = "free"

SUBSCRIPTION_STATUS = (
    ("waiting", _("Waiting")),
    ("canceled", _("Canceled")),
)

MALE = "male"
FEMALE = "female"
SEX = (
    (MALE, _("Male")),
    (FEMALE, _("Female")),
)

TAX_PAYER_CHOICES=[('tax_payer', ugettext(u"Yes")), ('not_tax_payer', ugettext("No"))]

WAITING = "waiting"
PAID = "paid"  # when there >= 3 confirmations and bitcoin client
ALMOST_PAID = "almost_paid" # when we are checking just transactions on network
APPROVED = "approved"
CANCELED = "canceled"
NO_MONEY_ARRIVED = "no_money_arrived"
NOT_ENOUGH_MONEY_ARRIVED = "not_enough_money_arrived"
SEEN = "seen"
HIDDEN = "hidden"
RUNNING = "running"

PAYMENT_STATUS = (
    (WAITING, _("Waiting")),
    (APPROVED, _("Approved")),
    (PAID, _("Paid")),
    (CANCELED, _("Canceled")),
    (NO_MONEY_ARRIVED, _("No money arrived")),
    (NOT_ENOUGH_MONEY_ARRIVED, _("Not enough money arrived")),
    (FREE, _("Free")),
    (FIRST_TIME, _("First time"))
)

CASH = "cash"

BILL_STATUS = (
    (WAITING, _("Awaiting payment")),
    (PAID, _("Paid")),
    (CANCELED, _("Canceled")),
)

BILL_FORMAT_OPTIONS = (  # the first is the default
    ("yyyy-s", _("Year and serial, resets every year")),
    ("s", _("Serial only, never resets")),
    ("yyyy-m-s", _("Year, month and serial, resets every month")),
)

TAX_PAYER_CHOICES = (
    ("yes", _("Yes")),
    ("no", _("No")),
    ("eu", _("EU")),
)