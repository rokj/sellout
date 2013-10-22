# coding=UTF-8
from django.utils.translation import ugettext as _

# Common stuff to be used anywhere throughout the site

# directories
DIRS = { # goes to MEDIA folder
    'logo_dir':"img/logo",
    'category_icon_dir':"img/category",
    'product_icon_dir':'img/product',
    'product_image_dir':"img/product",
}

# attributes' field lengths
ATTR_LEN = {
    'name':30,
    'value':100,
}

# number of digits for decimal database field
DECIMAL = {
    'currency_digits':16, # number of digits for money values (big money) (INCLUDING DECIMAL PLACES)
    'currency_decimal_places':4, # number of decimal places for money values
    'percentage_decimal_places':4, # number of decimal places for percentage values
    'quantity_digits':16,
    'quantity_decimal_places':4,
}

# unit types
# unicode superscripts: ² ³ (replacing ^* with <sup>*</sup> does not work for <select>)
UNITS = (
    ("Piece", _("Piece")),
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
)

# discounts
DISCOUNT_TYPES = (
    ("Percent", _("Percentage")),
    ("Absolute", _("Absolute value")),
)

DISCOUNT_CALCULATION = (
    ("Tax first", _("Add tax, then subtract discount")),
    ("Discount first", _("Subtract discount, then add tax")),
)

# contacts
CONTACT_TYPES = (
    ("Individual", _("Individual")),
    ("Company", _("Company")),
)

# bills
BILL_TYPES = ( 
    ("Normal",_("Normal")),
    # TODO add type for company
)

BILL_STATUS = (
    ("Active", _("Active")), # the bill that's currently open in POS (only one can exist!)
    ("Offer", _("Offer")), # ponudba # TODO preveriti izrazoslovje
    ("Quote", _("Quote")), # predracun
    ("Invoice", _("Invoice")), # racun
    ("Canceled", _("Canceled")),
)

# date formats
# specify all formats for each date:
#  - regular expression for checking format
#  - python's strftime format
#  - django templates
#  - jquery format string (for datepicker etc.)
DATE_FORMATS = {
    'dd.mm.yyyy':{'regex':"^\d{1,2}\.\d{1,2}\.\d{4}$", # with or without leading zeros
                  'python':"%d.%m.%Y", # the docs say zero-padded decimal, but will also parse non-padded numbers
                  'django':"j.n.Y", # show no leading zeros in template
                  'android':"dd-MM-yyyy",
                  'jquery':"dd.mm.yy",
                  },
    'mm/dd/yyyy':{'regex':"^\d{1,2}\.\d{1,2}\.\d{4}$", # with or without leading zeros
                  'python':"%m/%d/%Y",
                  'django':"n/j/Y",
                  'android':"MM-dd-yyyy",
                  'jquery':"mm/dd/yy",
                  },
    'yyyy-mm-dd':{'regex':"^\d{4}\.\d{2}\.\d{2}$", # strictly with leading zeros
                  'python':"%Y-%m-%d",
                  'django':"Y-m-d",
                  'android':"yyyy-MM-dd",
                  'jquery':"yy-mm-dd",
                  },
}

TIME_FORMATS = {
    '23:59':{ # 24-hour clock
            'regex':"^[0-2][0-4]:[0-5][0-9]$",
            'python':"%H:%M",
            'django':"H:i",
            'android':"hh:mm",
            'js':"HH:mm", # jquery has nothing to do with time, so it will have to be formatted using javascript
            },
    '23:59:59':{ # 24-hour clock with seconds
            'regex':"^[0-2][0-4]:[0-5][0-9]:[0-5][0-9]$",
            'python':"%H:%M:%S",
            'django':"H:i:s",
            'android':"hh:mm:ss",
            'js':"HH:mm:ss",
            },
    '12:59 AM/PM':{ # 12-hour clock with AM/PM
            'regex':"^[0-2][0-4]:[0-5][0-9] (AM|PM)$",
            'python':"%I:%M %p",
            'django':"",
            'android':"",
            'js':"hh:mm <AMPM>", # <AMPM> will have to be replaced in javascript (python?)
            },
    '12:59:59 AM/PM':{ # 12-hour clock with AM/PM
            'regex':"^[0-2][0-4]:[0-5][0-9]:[0-5][0-9] (AM|PM)$",
            'python':"%r",
            'django':"",
            'android':"",
            'js':"hh:mm:ss <AMPM>", # <AMPM> will have to be replaced in javascript (python?)
            },
}



DATE = {
    'max_date_length':10,
}


# misc
MISC = {
    'company_url_length':50,
    'site_title':'webpos',
    'management_url':'admin', # must not be empty!
                              # (to differentiate between company and management sites)
    'max_upload_image_size':2*2**20, # 2 megabytes
    'image_format':'png', # all images will be saved in this format
    'image_upload_formats':'jpg|jpeg|gif|png|bmp|tiff', # supported image formats (as regex "options")
}

IMAGE_DIMENSIONS = {
    'logo':(180, 180),
    'category':(160, 160),
    'product':(160,160), # must be as large as the largest PRODUCT_BUTTON_DIMENSIONS
    'thumb_small':(32, 32), # for thumbnails
    'thumb_large':(64, 64),
}

# premissions
PERMISSION_GROUPS = ( # retrieve readable format with get_permission_display()
    ('guest',   _("Guest")),   # can only view stuff
    ('cashier', _("Cashier")), # can write and edit bills
    ('seller',  _("Seller")),  # can add and edit products
    ('manager', _("Manager")), # can add and edit discounts, contacts, categories, ...
    ('admin',   _("Admin")),   # can do anything 
)

PERMISSIONS = { # 'chapters' that each group can view or manage
    # model choices: company, category, discount, product, contact, permission, bill, config
    # views (to prevent users exploring other companies' terminals):
    # manage, terminal
    'guest':{
        'list':('company','category','discount','product','contact','bill','tax',
            'terminal',),
        'edit':(),
        },
    'cashier':{
        'list':('company','category','discount','product','contact','bill','config','tax',
            'terminal',),
        'edit':('bill',
            'terminal','config',),
        },
    'seller':{
        'list':('company','category','discount','product','contact','bill','config','tax',
            'terminal','manage',),
        'edit':('bill','product',
            'terminal','manage','config','tax',),
        },
    'manager':{
        'list':('company','category','discount','product','contact','bill','permission','config','tax',
            'terminal','manage',),
        'edit':('category','discount','product','contact','bill','config','tax',
            'terminal','manage',),
        },
    'admin':{
        'list':('company','category','discount','product','contact','bill', 'permission','config',
            'terminal','manage','tax',),
        'edit':('company','category','discount','product','contact','bill', 'permission','config',
            'terminal','manage','tax',),
        },
}

### terminal page configuration ###
INTERFACES = [
    'touch', # also for mouse (first entry is default)
    'keyboard',
]

PRODUCT_BUTTON_DIMENSIONS = {
    'small':90, # all squares
    'medium':125,
    'large':160 # check IMAGE_DIMENSIONS['product']
}
