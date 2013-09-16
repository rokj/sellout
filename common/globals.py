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
    'currency_digits':12, # number of digits for money values (big money) (INCLUDING DECIMAL PLACES)
    'currency_decimal_places':4, # number of decimal places for money values
    'percentage_decimal_places':4, # number of decimal places for percentage values
    'quantity_digits':9,
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

# contacts
CONTACT_TYPES = (
    ("Individual", _("Individual")),
    ("Company", _("Company")),
)

# bills
# TODO popraviti izrazoslovje
BILL_TYPES = (
    ("asdf",_("krneki")),
)

BILL_STATUS = (
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
    'dd.mm.yyyy':{'regex':"\d{1,2}\.\d{1,2}\.\d{4}", # with or without leading zeros
                  'python':"%d.%m.%Y", # the docs say zero-padded decimal, but will also parse non-padded numbers
                  'django':"j.n.Y", # show no leading zeros in template
                  'jquery':"dd.mm.yy",
                  },
    'mm/dd/yyyy':{'regex':"\d{1,2}\.\d{1,2}\.\d{4}", # with or without leading zeros
                  'python':"%m/%d/%Y",
                  'django':"n/j/Y",
                  'jquery':"mm/dd/yy",
                  },
    'yyyy-mm-dd':{'regex':"\d{4}\.\d{2}\.\d{2}", # strictly with leading zeros
                  'python':"%Y-%m-%d",
                  'django':"Y-m-d",
                  'jquery':"yy-mm-dd",
                  },
}

# misc
MISC = {
    'company_url_length':50,
    'site_title':'webpos',
    'management_url':'admin', # must not be empty!
                              # (to differentiate between company and management sites)
    'max_upload_image_size':2*2**20, # 2 megabytes
    'image_format':'png', # all images will be saved in this format
}

IMAGE_DIMENSIONS = {
    'logo':(180, 180),
    'category':(160, 160),
    'product':(120,120),
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
    # choices: company, category, discount, product, contact, permission, bill
    'guest':{
        'list':('company','category','discount','product','contact','bill'),
        'edit':(),
        },
    'cashier':{
        'list':('company','category','discount','product','contact','bill'),
        'edit':('bill'),
        },
    'seller':{
        'list':('company','category','discount','product','contact','bill'),
        'edit':('bill','product'),
        },
    'manager':{
        'list':('company','category','discount','product','contact','bill','permission'),
        'edit':('category','discount','product','contact','bill'),
        },
    'admin':{
        'list':('company','category','discount','product','contact','bill', 'permission'),
        'edit':('company','category','discount','product','contact','bill', 'permission'),
        },
}