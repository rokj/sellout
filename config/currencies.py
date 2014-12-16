# -*- coding: UTF-8 -*-
currencies = {
    "USD": ("United stats dollar", "$"),
    "EUR": ("Euro", "€"),
    "JPY": ("Japanese yen", "¥"),
    "GBP": ("Pound sterling", "£"),
    "AUD": ("Australian dollar", "$"),
    "CHF": ("Swiss franc", "Fr"),
    "CAD": ("Canadian dollar", "$"),
    "CNY": ("Chinese yuan", "¥"),
}

currency_choices = tuple((key, key + " (" + value[0] + ")") for key, value in currencies.iteritems())