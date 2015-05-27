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
    document = models.ForeignKey(Document, null=True, blank=True)
    company = models.ForeignKey(Company, null=False, blank=False)
    for_product = models.ForeignKey(Product, help_text=_("For product"), null=False, blank=False)
    name = models.CharField(_("Name"), help_text=_("Name of a stock"), max_length=100, null=True, blank=True)
    quantity = models.DecimalField(_("Number of items put in stock"),
        max_digits=g.DECIMAL['quantity_digits'],
        decimal_places=g.DECIMAL['quantity_decimal_places'],
        null=False, blank=False)
    stock = models.DecimalField(_("Stock"),
        max_digits=g.DECIMAL['quantity_digits'],
        decimal_places=g.DECIMAL['quantity_decimal_places'],
        null=False, blank=False)
    left_stock = models.DecimalField(_("Number of items left in stock"),
        max_digits=g.DECIMAL['quantity_digits'],
        decimal_places=g.DECIMAL['quantity_decimal_places'],
        null=False, blank=False)
    stock_type = models.CharField(_("Stock type"), max_length=10,
        choices=g.STOCK_TYPE, blank=False, null=False, default=g.STOCK_TYPE[0][0])
    unit_type = models.CharField(_("Product unit type"), max_length=15,
        choices=g.UNITS, blank=False, null=False, default=g.UNITS[0][0])


    @property
    def purchase_price(self):
        return self.get_purchase_price()

    def get_purchase_price(self):
        """ get product's current purchase price """
        try:
            return PurchasePrice.objects.filter(stock_item=self).order_by('-datetime_updated')[0].unit_price
        except:
            return None

class PurchasePrice(SkeletonU):
    unit_price = models.DecimalField(_("Purchase price per unit, excluding tax"), max_digits=g.DECIMAL['currency_digits'],
                                     decimal_places=g.DECIMAL['currency_decimal_places'], blank=False, null=False)
    stock_item = models.ForeignKey(Stock)

    def __unicode__(self):
        ret = self.stock_item + ": " + str(self.unit_price)

        if self.datetime_updated:
            ret += " (inactive)"

        return ret

    class Meta:
        unique_together = (('stock_item', 'unit_price', 'datetime_updated'),)



