# -*- coding: UTF-8 -*-
from django.utils.translation import ugettext as _

currencies = {
    "USD": (_("United States Dollar"), "$"),
    "EUR": (_("Euro"), "€"),
    "JPY": (_("Japanese Yen"), "¥"),
    "GBP": (_("Pound Sterling"), "£"),
    "AUD": (_("Australian Dollar"), "$"),
    "CHF": (_("Swiss Franc"), "Fr"),
    "CAD": (_("Canadian Dollar"), "$"),
    "CNY": (_("Chinese Yuan"), "¥"),
}

default_currency = "USD"

currency_choices = tuple((key, key + " (" + value[0] + ")") for key, value in currencies.iteritems())