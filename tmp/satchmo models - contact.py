class Organization(models.Model):
    """
    An organization can be a company, government or any kind of group.
    """
    name = models.CharField(_("Name"), max_length=50, )
    type = models.ForeignKey(ContactOrganization, verbose_name=_("Type"), null=True)
    role = models.ForeignKey(ContactOrganizationRole, verbose_name=_("Role"), null=True)
    create_date = models.DateField(_("Creation Date"))
    notes = models.TextField(_("Notes"), max_length=200, blank=True, null=True)



class Contact(models.Model):
    """
    A customer, supplier or any individual that a store owner might interact
    with.
    """
    title = models.CharField(_("Title"), max_length=30, blank=True, null=True)
    first_name = models.CharField(_("First name"), max_length=30, )
    last_name = models.CharField(_("Last name"), max_length=30, )
    user = models.ForeignKey(User, blank=True, null=True, unique=True)
    role = models.ForeignKey(ContactRole, verbose_name=_("Role"), null=True)
    organization = models.ForeignKey(Organization, verbose_name=_("Organization"), blank=True, null=True)
    dob = models.DateField(_("Date of birth"), blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, max_length=75)
    notes = models.TextField(_("Notes"), max_length=500, blank=True)
    create_date = models.DateField(_("Creation date"))

class AddressBook(models.Model):
    """
    Address information associated with a contact.
    """
    contact = models.ForeignKey(Contact)
    description = models.CharField(_("Description"), max_length=20, blank=True,
        help_text=_('Description of address - Home, Office, Warehouse, etc.',))
    addressee = models.CharField(_("Addressee"), max_length=80)
    street1 = models.CharField(_("Street"), max_length=80)
    street2 = models.CharField(_("Street"), max_length=80, blank=True)
    state = models.CharField(_("State"), max_length=50, blank=True)
    city = models.CharField(_("City"), max_length=50)
    postal_code = models.CharField(_("Zip Code"), max_length=30)
    country = models.ForeignKey(Country, verbose_name=_("Country"))
    is_default_shipping = models.BooleanField(_("Default Shipping Address"),
        default=False)
    is_default_billing = models.BooleanField(_("Default Billing Address"),
        default=False)

