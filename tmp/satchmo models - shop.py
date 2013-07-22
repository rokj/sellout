# informacije o trgovini

class Config(models.Model):
    """
    Used to store specific information about a store.  Also used to
    configure various store behaviors
    """
    site = models.OneToOneField(Site, verbose_name=_("Site"), primary_key=True)
    store_name = models.CharField(_("Store Name"),max_length=100, unique=True)
    store_description = models.TextField(_("Description"), blank=True, null=True)
    store_email = models.EmailField(_("Email"), blank=True, null=True, max_length=75)
    street1=models.CharField(_("Street"),max_length=50, blank=True, null=True)
    street2=models.CharField(_("Street"), max_length=50, blank=True, null=True)
    city=models.CharField(_("City"), max_length=50, blank=True, null=True)
    state=models.CharField(_("State"), max_length=30, blank=True, null=True)
    postal_code=models.CharField(_("Zip Code"), blank=True, null=True, max_length=9)
    country=models.ForeignKey(Country, blank=False, null=False, verbose_name=_("Country"))
    phone = models.CharField(_("Phone Number"), blank=True, null=True, max_length=30)


# racun
class Order(models.Model):
    """
    Orders contain a copy of all the information at the time the order was
    placed.
    """
    site = models.ForeignKey(Site, verbose_name=_('Site'))
    contact = models.ForeignKey(Contact, verbose_name=_('Contact'))
    ship_addressee = models.CharField(_("Addressee"), max_length=61, blank=True)
    ship_street1 = models.CharField(_("Street"), max_length=80, blank=True)
    ship_street2 = models.CharField(_("Street"), max_length=80, blank=True)
    ship_city = models.CharField(_("City"), max_length=50, blank=True)
    ship_state = models.CharField(_("State"), max_length=50, blank=True)
    ship_postal_code = models.CharField(_("Zip Code"), max_length=30, blank=True)
    ship_country = models.CharField(_("Country"), max_length=2, blank=True)
    bill_addressee = models.CharField(_("Addressee"), max_length=61, blank=True)
    bill_street1 = models.CharField(_("Street"), max_length=80, blank=True)
    bill_street2 = models.CharField(_("Street"), max_length=80, blank=True)
    bill_city = models.CharField(_("City"), max_length=50, blank=True)
    bill_state = models.CharField(_("State"), max_length=50, blank=True)
    bill_postal_code = models.CharField(_("Zip Code"), max_length=30, blank=True)
    bill_country = models.CharField(_("Country"), max_length=2, blank=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    sub_total = CurrencyField(_("Subtotal"),
        max_digits=18, decimal_places=10, blank=True, null=True, display_decimal=4)
    total = CurrencyField(_("Total"),
        max_digits=18, decimal_places=10, blank=True, null=True, display_decimal=4)
    discount_code = models.CharField(
        _("Discount Code"), max_length=20, blank=True, null=True,
        help_text=_("Coupon Code"))
    discount = CurrencyField(_("Discount amount"),
        max_digits=18, decimal_places=10, blank=True, null=True)
    method = models.CharField(_("Order method"),
        choices=ORDER_CHOICES, max_length=50, blank=True)
    shipping_description = models.CharField(_("Shipping Description"),
        max_length=200, blank=True, null=True)
    shipping_method = models.CharField(_("Shipping Method"),
        max_length=200, blank=True, null=True)
    shipping_model = models.CharField(_("Shipping Models"), choices=iterchoices_db(shipping.fields.shipping_choices),
        max_length=30, blank=True, null=True)
    shipping_cost = CurrencyField(_("Shipping Cost"),
        max_digits=18, decimal_places=10, blank=True, null=True)
    shipping_discount = CurrencyField(_("Shipping Discount"),
        max_digits=18, decimal_places=10, blank=True, null=True)
    tax = CurrencyField(_("Tax"),
        max_digits=18, decimal_places=10, blank=True, null=True)
    time_stamp = models.DateTimeField(_("Timestamp"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=ORDER_STATUS,
        blank=True, help_text=_("This is set automatically."))

class OrderItem(models.Model):
    """
    A line item on an order.
    """
    order = models.ForeignKey(Order, verbose_name=_("Order"))
    product = models.ForeignKey(Product, verbose_name=_("Product"), on_delete=models.PROTECT)
    quantity = models.DecimalField(_("Quantity"),  max_digits=18,  decimal_places=6)
    unit_price = CurrencyField(_("Unit price"),
        max_digits=18, decimal_places=10)
    unit_tax = CurrencyField(_("Unit tax"), default=Decimal('0.00'),
        max_digits=18, decimal_places=10)
    line_item_price = CurrencyField(_("Line item price"),
        max_digits=18, decimal_places=10)
    tax = CurrencyField(_("Line item tax"), default=Decimal('0.00'),
        max_digits=18, decimal_places=10)
    expire_date = models.DateField(_("Subscription End"), help_text=_("Subscription expiration date."), blank=True, null=True)
    completed = models.BooleanField(_("Completed"), default=False)
    discount = CurrencyField(_("Line item discount"),
        max_digits=18, decimal_places=10, blank=True, null=True)


class OrderItemDetail(models.Model):
    """
    Name, value pair and price delta associated with a specific item in an order
    """
    item = models.ForeignKey(OrderItem, verbose_name=_("Order Item"), )
    name = models.CharField(_('Name'), max_length=100)
    value = models.CharField(_('Value'), max_length=255)
    price_change = CurrencyField(_("Price Change"), max_digits=18, decimal_places=10, blank=True, null=True)
    sort_order = models.IntegerField(_("Sort Order"),
        help_text=_("The display order for this group."))


class OrderStatus(models.Model):
    """
    An order will have multiple statuses as it moves its way through processing.
    """
    order = models.ForeignKey(Order, verbose_name=_("Order"))
    status = models.CharField(_("Status"),
        max_length=20, choices=ORDER_STATUS, blank=True)
    notes = models.CharField(_("Notes"), max_length=100, blank=True)
    time_stamp = models.DateTimeField(_("Timestamp"))


class OrderPaymentBase(models.Model):
    payment = models.CharField(_("Payment Method"), choices=iterchoices_db(payment.config.labelled_gateway_choices),
        max_length=25, blank=True)
    amount = CurrencyField(_("amount"),
        max_digits=18, decimal_places=10, blank=True, null=True)
    time_stamp = models.DateTimeField(_("timestamp"), blank=True, null=True)
    transaction_id = models.CharField(_("Transaction ID"), max_length=45, blank=True, null=True)
    details = models.CharField(_("Details"), max_length=255, blank=True, null=True)
    reason_code = models.CharField(_('Reason Code'),  max_length=255, blank=True, null=True)

class OrderAuthorization(OrderPaymentBase):
    order = models.ForeignKey(Order, related_name="authorizations")
    capture = models.ForeignKey('OrderPayment', related_name="authorizations")
    complete = models.BooleanField(_('Complete'), default=False)
