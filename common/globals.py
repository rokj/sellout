from django.utils.translation import ugettext as _

# Common stuff to be used anywhere throughout the site

# directories
DIRS = {
        'logo_dir':"img/logo",
        'category_icon_dir':"img/category",
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
UNITS = (
    ("Piece", _("Piece")),
    ("g", "g"),
    ("dag", "dag"),
    ("kg", "kg"),
    ("oz", "oz"),
    ("lb", "lb"),
    ("cm", "cm"),
    ("m", "m"),
    ("in", "in"),
    ("ft", "ft"),
    ("yd", "yd"),
    ("in^2", "in^2"),
    ("m^2", "m^2"),
    ("ft^2", "ft^2"),
    ("l", "l"),
    ("dl", "dl"),
    ("cl", "cl"),
    ("m^3", "m^3"),
    ("fl. oz.", "fl. oz."),
    ("pint", "pint"),
    ("gal", "gal"),
    ("ft^3", "ft^3"),
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

# misc
MISC = {
        'company_url_length':50,
        'site_title':'webpos',
        }