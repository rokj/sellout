from django.db import models

from django.utils.translation import ugettext as _

from config.countries import country_choices, country_by_code
import common.globals as g

class ContactRegistry(models.Model):
    # this is used for storing contacs, business entities from busniess information authorities
    # e.g. in Slovenia there is AJPES and DURS which provide information about busniess entities
    type = models.CharField(_("Type of contact"), max_length=20, choices=g.CONTACT_TYPES,
                            null=False, blank=False, default=g.CONTACT_TYPES[0][0])
    company_name = models.CharField(_("Company name"), max_length=50, null=True, blank=True)
    first_name = models.CharField(_("First name"), max_length=50, null=True, blank=True)
    last_name = models.CharField(_("Last name"), max_length=50, null=True, blank=True)
    sex = models.CharField(max_length=1, choices=g.SEXES, null=True, blank=True)
    date_of_birth = models.DateField(_("Date of birth"), null=True, blank=True)
    street_address = models.CharField(_("Street and house number"), max_length=200, null=True, blank=True)
    postcode = models.CharField(_("Post code/ZIP"), max_length=12, null=True, blank=True)
    city = models.CharField(_("City"), max_length=50, null=True, blank=True)
    state = models.CharField(_("State"), max_length=50, null=True, blank=True)
    country = models.CharField(max_length=2, choices=country_choices)
    email = models.CharField(_("E-mail address"), max_length=255, blank=True, null=True)
    phone = models.CharField(_("Telephone number"), max_length=30, blank=True, null=True)
    vat = models.CharField(_("VAT identification number"), max_length=30, null=True, blank=True, unique=True)
    tax_payer = models.CharField(_("Tax payer"), max_length=3, choices=g.TAX_PAYER_CHOICES, blank=False, null=False, default="no")
    additional_info = models.TextField(blank=True, null=True)

    @property
    def country_name(self):
        return country_by_code.get(self.country)

    def __unicode__(self):
        if self.type == "Individual":
            return "Individual: " + self.first_name + " " + self.last_name
        else:
            return "Company: " + str(self.company_name)
