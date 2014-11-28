# -*- coding:utf-8 -*-
import django
from django.core.urlresolvers import reverse
from django.db import models
from django.template import defaultfilters
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from common.globals import WAITING, PAYMENT_STATUS, FREE

from common.models import SkeletonU, Currency, Country
from settings import PAYMENT
import settings
from subscription.models import Subscription, Subscriptions

from decimal import Decimal

import json


class Payment(SkeletonU):
    type = models.CharField(_("Payment type"), help_text=_("Payment made with"), default=FREE,
                            choices=tuple([tuple([key, _(key.title())]) for key in [key for key in PAYMENT.keys()]]),
                            max_length=20, null=False, blank=False)
    amount_paid = models.DecimalField(_("Amount paid"), default=0, blank=False, null=False, decimal_places=8,
                                      max_digits=40)
    currency = models.ForeignKey(Currency, null=True, blank=True)
    total = models.DecimalField(_("Total amount in EUR for BTC or in currency to be paid"), null=True,
                                blank=True, decimal_places=20, max_digits=40)
    total_btc = models.DecimalField(_("Total amount in BTC to be paid"), null=True, blank=True,
                                decimal_places=20, max_digits=40)
    transaction_datetime = models.DateTimeField(_("Date and time of transaction"), null=True, blank=True)
    transaction_reference = models.CharField(_("Reference for payer"), help_text=_("BTC address or Sklic or unique ID"
                                                                                   "for authorization/cancelation"),
                                           max_length=150, blank=True, null=True, unique=True)
    payment_info = models.TextField(_("Info about payment"), blank=True, null=True)
    subscription = models.ManyToManyField(Subscription)
    status = models.CharField(_("Payment status"), default=WAITING, choices=PAYMENT_STATUS, max_length=30,
                              null=False, blank=False)

    __unicode__ = lambda self:  u'%s %s %s' % (self.type, self.amount_paid, self.status)

    def me_included_in_payment(self, user):
        if self.created_by == user:
            for s in self.subscription.all():
                if s.user and s.user == user:
                    return True

        return False

    def other_users_included_in_payment(self, user):
        users_included = []

        if self.created_by == user:
            for s in self.subscription.all():
                # if users who is getting this information is not equal
                if s.user and s.user != user:
                    users_included.append(s.user.email)
                elif s.email and s.email != "" and s.email != user.email:
                    users_included.append(s.email)

        if len(users_included) > 0:
            users_included.sort()

        return users_included

    def _parse_message_html(self):
        from django.template.defaultfilters import floatformat

        file = open(settings.STATIC_DIR + "email/payment/invoice.html", "r")
        message_html = file.read()
        file.close()

        payment_url = settings.SITE_URL.strip("/") + reverse("subscription:subscriptions") + "#payment-info/" + str(self.id)

        # FOR FUTURE
        name = u''
        address = u''
        postal_code = u''
        country = u''
        tax_id = u''
        postal_info = u''
        vat_disclaimer = _('VAT is not charged according to Article 94 of Slovenian VAT act (ZDDV-1).')

        payment_info = json.loads(self.payment_info)
        if "company_name" in payment_info:
            name = payment_info["company_name"]
            vat_disclaimer = _('VAT is not charged according to Article 44 of European VAT directive - reverse charge for recipient.')

            if "company_address" in payment_info:
                address = payment_info["company_address"]
            if "company_postcode" in payment_info and "company_city" in payment_info:
                postal_info = payment_info["company_postcode"] + " " + payment_info["company_city"]
            if "company_country" in payment_info:
                try:
                    c = Country.objects.get(two_letter_code=payment_info["company_country"])
                    country = c.name
                except Country.DoesNotExist:
                    pass

            if "company_tax_id" in payment_info:
                tax_id = payment_info["company_tax_id"]

        else:
            name = self.created_by.first_name + " " + self.created_by.last_name
            address = u''
            postal_code = u''
            country = u''

        nr_people_included = len(self.other_users_included_in_payment(self.created_by))

        if self.me_included_in_payment(self.created_by):
            nr_people_included += 1

        if nr_people_included == 1:
            people = _("Paid for 1 person")
        else:
            people = _("Paid for %s persons" % nr_people_included)

        duration = _("1 month")
        if self.subscription_duration > 1:
            duration = _("%s months" % self.subscription_duration)

        if self.type == "bitcoin":
            message_html = message_html.format(
                floatformat(self.total_btc, 8),
                settings.SITE_URL,
                settings.COMPANY["name"],
                settings.COMPANY["address"] + "<br>" + settings.COMPANY["postal_code"] + " " + settings.COMPANY["city"] + "<br>" + settings.COMPANY["country"],
                settings.COMPANY["phone_number"],
                settings.COMPANY["email"],
                settings.COMPANY["website"].replace("http://www.", ""),
                settings.COMPANY["iban"],
                settings.COMPANY["registration_number"],
                settings.COMPANY["tax_number"],
                name.encode("utf-8"), # {10}
                address.encode("utf-8"), # {11}
                postal_info.encode("utf-8"), # {12}
                country.encode("utf-8"), # {13}
                tax_id.encode("utf-8"), # {14}
                unicode(self.id).encode("utf-8"),
                defaultfilters.date(self.transaction_datetime, "Y-m-d"),
                self.type.encode("utf-8"),
                people.encode("utf-8"),
                unicode(self.id).encode("utf-8"),
                duration.encode("utf-8"),
                floatformat(self.total-Decimal(self.transaction_fee), 2),
                floatformat(Decimal(self.transaction_fee), 2),
                floatformat(self.total, 2) + "&euro;" + " (" + floatformat(self.total_btc, 8) + " BTC)",
                payment_url.encode("utf-8"), # {24}
                vat_disclaimer.encode("utf-8") # {25}
            )
        # paypal or sepa
        else:
            message_html = message_html.format(
                floatformat(self.total_btc, 8),
                settings.SITE_URL,
                settings.COMPANY["name"],
                settings.COMPANY["address"] + "<br>" + settings.COMPANY["postal_code"] + " " + settings.COMPANY["city"] + "<br>" + settings.COMPANY["country"],
                settings.COMPANY["phone_number"],
                settings.COMPANY["email"],
                settings.COMPANY["website"].replace("http://www.", ""),
                settings.COMPANY["iban"],
                settings.COMPANY["registration_number"],
                settings.COMPANY["tax_number"],
                name.encode("utf-8"), # {10}
                address.encode("utf-8"), # {11}
                postal_info.encode("utf-8"), # {12}
                country.encode("utf-8"), # {13}
                tax_id.encode("utf-8"), # {14}
                unicode(self.id).encode("utf-8"),
                defaultfilters.date(self.transaction_datetime, "Y-m-d"),
                self.type.encode("utf-8"),
                people.encode("utf-8"),
                unicode(self.id).encode("utf-8"),
                duration.encode("utf-8"),
                floatformat(self.total-Decimal(self.transaction_fee), 2),
                floatformat(Decimal(self.transaction_fee), 2),
                floatformat(self.total, 2) + "&euro;",
                payment_url.encode("utf-8"), # {24}
                vat_disclaimer.encode("utf-8") # {25}
            )

        return message_html


    def send_payment_confirmation_email(self):
        from common.functions import send_email
        from django.template.defaultfilters import floatformat

        payment_url = settings.SITE_URL.strip("/") + reverse("subscription:subscriptions") + "#payment-info/" + str(self.id)

        # TXT
        if self.type == "bitcoin":
            file = open(settings.STATIC_DIR + "email/payment/payment_received_btc_" + django.utils.translation.get_language() + ".txt", "r")
        else:
            file = open(settings.STATIC_DIR + "email/payment/payment_received_euros_" + django.utils.translation.get_language() + ".txt", "r")
        message_txt = file.read()
        file.close()

        if self.type == "bitcoin":
            message_txt = message_txt % (floatformat(self.total_btc, 8), payment_url, settings.SITE_URL)
        else:
            message_txt = message_txt % (floatformat(self.total, 2), payment_url, settings.SITE_URL)

        # HTML
        message_html = self._parse_message_html()

        subject = _("%s - Payment received" % ("timebits.com"))
        if settings.DEBUG:
            print "Will send confirmation email about payment now..."
            print "It will look like this"
            print "START ------------------------ START"
            print message_html
            print "END ---------------------------- END"
        send_email(settings.EMAIL_FROM, [self.created_by.email], [settings.SENT_EMAILS_ACC], subject, message_txt, message_html)

    @property
    def subscription_duration(self):
        payment_info = json.loads(self.payment_info)

        return payment_info["subscription_duration"]

    @property
    def payment_date(self):
        # maybe not needed at all
        # since we have transaction datetime
        payment_info = json.loads(self.payment_info)

        return payment_info["payment_date"]

    @property
    def transaction_fee(self):
        payment_info = json.loads(self.payment_info)
        if "transaction_fee" in payment_info:
            return payment_info["transaction_fee"]

        return 0

    @property
    def paypal_payment_link(self):
        payment_info = json.loads(self.payment_info)

        if payment_info and "links" in payment_info:
            for link in payment_info["links"]:
                if link["rel"] == "approval_url":
                    return link["href"]

        return ""
