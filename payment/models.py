# -*- coding:utf-8 -*-
import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from common.functions import calculate_btc_price
from common.globals import WAITING, PAYMENT_STATUS, CASH, DECIMAL

from common.models import SkeletonU
from config.currencies import currency_choices
from config.functions import get_company_value
from payment.service.Bitcoin import BitcoinRPC
from settings import PAYMENT
import settings


class Payment(SkeletonU):
    type = models.CharField(_("Payment type"), help_text=_("Payment made with"), default=CASH,
                            choices=tuple([tuple([key, _(key.title())]) for key in [key for key in PAYMENT.keys()]]),
                            max_length=20, null=False, blank=False)
    amount_paid = models.DecimalField(_("Amount paid"), default=0, blank=False, null=False, decimal_places=8,
                                      max_digits=40)
    currency = models.CharField(max_length=3, choices=currency_choices, null=True, blank=True, default="USD")
    total = models.DecimalField(
        _("Total amount to be paid"),
        max_digits=DECIMAL['currency_digits'],
        decimal_places=DECIMAL['currency_decimal_places'],
        null=True, blank=True)
    total_btc = models.DecimalField(
        _("Total amount in BTC to be paid"),
        max_digits=DECIMAL['currency_digits'],
        decimal_places=DECIMAL['currency_decimal_places'],
        null=True, blank=True
    )
    transaction_datetime = models.DateTimeField(_("Date and time of transaction"), null=True, blank=True)
    btc_transaction_reference = models.CharField(_("BTC transaction reference"), help_text=_("BTC address"),
                                           max_length=150, blank=True, null=True, unique=True)
    paypal_transaction_reference = models.CharField(_("Paypal transaction reference"), help_text=_("Its actually paypal invoice id"),
                                           max_length=150, blank=True, null=True, unique=True)

    payment_info = models.TextField(_("Info about payment"), blank=True, null=True)
    status = models.CharField(_("Payment status"), default=WAITING, choices=PAYMENT_STATUS, max_length=30,
                              null=False, blank=False)

    def get_btc_address(self, company_id):
        if self.pk and self.pk is not None:
            if self.btc_transaction_reference is not None and self.btc_transaction_reference != "":
                return self.btc_transaction_reference
            else:
                bitcoin_rpc = BitcoinRPC(settings.PAYMENT['bitcoin']['host'], settings.PAYMENT['bitcoin']['port'],
                                         settings.PAYMENT['bitcoin']['rpcuser'], settings.PAYMENT['bitcoin']['rpcpassword'])
                address = bitcoin_rpc.get_new_address(settings.PAYMENT['bitcoin']['account_prefix'] + str(company_id))

                self.btc_transaction_reference = address
                self.save()

                return address

        return ""

    def get_btc_amount(self, user, company):
        """
        This method should be used when paying, otherwise get amount from self.total_btc
        """

        datetime_updated_with_offset = self.datetime_updated + datetime.timedelta(hours=int(settings.PAYMENT_OFFICER["bitcoin_payment_waiting_interval"]))

        if self.status == WAITING:
            if self.total_btc is None or datetime_updated_with_offset < datetime.datetime.now():
                currency = get_company_value(user, company, 'pos_currency')

                btc_price = calculate_btc_price(currency, self.total)

                if btc_price != -1:
                    self.total_btc = btc_price
                    self.save()

        return self.total_btc