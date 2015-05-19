# -*- coding:utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from common.models import SkeletonU
from pos.models import Contact, Company, Product

import common.globals as g

class Document(SkeletonU):
    company = models.ForeignKey(Company, null=False, blank=False)
    number = models.CharField(max_length=64, null=True)
    document_date = models.DateField(_("Document date"), null=True, blank=True)
    entry_date = models.DateField(_("Entry date"), null=True, blank=True)
    supplier = models.ForeignKey(Contact, null=False, blank=False)

class Stock(SkeletonU):
    document = models.ForeignKey(Document, null=False, blank=False)
    company = models.ForeignKey(Company, null=False, blank=False)
    product = models.ForeignKey(Product, help_text=_("From your products"), null=True, blank=True)
    ingridient = models.CharField(_("Ingridient"), help_text=_("Product or ingridient used for creating product"), max_length=100, null=True, blank=True)
    unit_type = models.CharField(_("Product unit type"), max_length=15,
        choices=g.UNITS, blank=False, null=False, default=g.UNITS[0][0])
    stock = models.DecimalField(_("Number of items left in stock"),
        max_digits=g.DECIMAL['quantity_digits'],
        decimal_places=g.DECIMAL['quantity_decimal_places'],
        null=False, blank=False)


