from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver
from sorl import thumbnail
from blusers.models import BlocklogicUser
from common.functions import ImagePath

from common.models import SkeletonU
import common.globals as g

from config.countries import country_choices, country_by_code

import datetime as dtm
import random


### company ###

class CompanyAbstract(models.Model):
    # abstract: used in  for Company and BillCompany
    name = models.CharField(_("Company name"), max_length=200, null=False, blank=False)
    street = models.CharField(_("Street address"), max_length=200, null=False, blank=False)
    postcode = models.CharField(_("Postal code"), max_length=20, null=False, blank=False)
    city = models.CharField(_("City"), max_length=50, null=False, blank=False)
    state = models.CharField(_("State"), max_length=50, null=True, blank=True)
    country = models.CharField(max_length=2, choices=country_choices, null=True, blank=True)
    email = models.CharField(_("E-mail address"), max_length=256, null=False, blank=False)
    website = models.CharField(_("Website"), max_length=256, null=True, blank=True)
    phone = models.CharField(_("Phone number"), max_length=30, null=True, blank=True)
    vat_no = models.CharField(_("VAT exemption number"), max_length=30, null=False, blank=False)

    tax_payer = models.BooleanField(_("Tax payer"), blank=False, null=False, default=False)

    class Meta:
        abstract = True

    @property
    def country_name(self):
        return country_by_code.get(self.country)


class Company(SkeletonU, CompanyAbstract):
    url_name = models.SlugField(_("Company name, used in URL address"),
                                max_length=g.MISC['company_url_length'],
                                null=False, blank=False, db_index=True)
    color_logo = thumbnail.ImageField(_("Logo"),
                                   upload_to=ImagePath(g.DIRS['color_logo_dir'],
                                                       "pos_company", "color_logo"),
                                   null=True, blank=True)
    monochrome_logo = thumbnail.ImageField(_("Receipt logo"),
                                        upload_to=ImagePath(g.DIRS['monochrome_logo_dir'],
                                                                 "pos_company", "monochrome_logo"),
                                        null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)

    # will be used for 'deleting' companies (marking them inactive)
    # TODO: create custom DeletedManager for querysets that leaves out deleted=True
    deleted = models.BooleanField(null=False, blank=False, default=False)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = _("Companies")

### category ###
class Category(SkeletonU):
    company = models.ForeignKey(Company, null=False, blank=False)
    parent = models.ForeignKey('self', blank=True, null=True)
    name = models.CharField(_("Category name"), max_length=100, null=False, blank=False)
    description = models.TextField(_("Description"), null=True, blank=True)
    color = models.CharField(default=g.CATEGORY_COLORS[0], blank=False, null=False, max_length=6)

    # image has been replaced by color
    # image = models.ImageField(_("Icon"),
    #                          upload_to=get_image_path(g.DIRS['category_icon_dir'], "pos_category", "image"),
    #                          null=True, blank=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = _("Categories")

    @property
    def breadcrumbs(self):
        name_breadcrumbs = ""
        id_breadcrumbs = []

        current_category = self

        while current_category is not None:
            name_breadcrumbs = current_category.name + name_breadcrumbs
            id_breadcrumbs.append(current_category.id)

            current_category = current_category.parent
            if current_category:
                name_breadcrumbs = " > " + name_breadcrumbs

        id_breadcrumbs.reverse()

        return {
            'name': name_breadcrumbs,
            'id': id_breadcrumbs,
        }

    @property
    def product_count(self):
        return Product.objects.filter(company=self.company, category=self).count()

    @property
    def category_level(self):
        i = 1
        cur_category = self
        while cur_category.parent is not None:
            i += 1
            cur_category = cur_category.parent
        return i


### discounts ###
class DiscountAbstract(models.Model):
    # used on Discount and BillItemDiscount
    description = models.TextField(_("Discount description"), null=True, blank=True)
    code = models.CharField(_("Code"), max_length=50, null=True, blank=True)
    type = models.CharField(_("Discount type"), max_length=30, choices=g.DISCOUNT_TYPES, null=False, blank=False,
                            default=g.DISCOUNT_TYPES[0][0])
    amount = models.DecimalField(_("Amount"),
                                 max_digits=g.DECIMAL['currency_digits'],
                                 decimal_places=g.DECIMAL['currency_decimal_places'],
                                 null=False, blank=False)

    class Meta:
        abstract = True


class Discount(SkeletonU, DiscountAbstract):
    company = models.ForeignKey(Company)

    start_date = models.DateField(_("Start date"), null=True, blank=True)
    end_date = models.DateField(_("End date"), null=True, blank=True)
    enabled = models.BooleanField(_("Enabled"), null=False, blank=True, default=True)

    class Meta:
        unique_together = (('company', 'code'))
    
    def __unicode__(self):
        return self.code + " " + self.description

    @property
    def is_active(self):
        today = dtm.date.today()

        if not self.enabled:
            return False

        valid = False

        if not self.start_date and not self.end_date:
            valid = True
        elif self.start_date and not self.end_date:
            if self.start_date <= today:
                valid = True
        elif not self.start_date and self.end_date:
            if self.end_date >= today:
                valid = True
        elif self.start_date and self.end_date:
            if self.start_date <= today <= self.end_date:
                valid = True

        return valid


### tax rates ###
class Tax(SkeletonU):
    company = models.ForeignKey(Company, null=False, blank=False)
    amount = models.DecimalField(_("Tax amount"), max_digits=g.DECIMAL['percentage_decimal_places']+3,
                          decimal_places=g.DECIMAL['percentage_decimal_places'], null=False, blank=False)
    name = models.CharField(_("Name"), max_length=15, null=True, blank=True)
    default = models.BooleanField(_("Use by default when creating new products"), default=False)
    
    class Meta:
        verbose_name_plural = _("Taxes")
        
    def __unicode__(self):
        return self.company.name + ": " + self.name


class ProductAbstract(models.Model):
    # used on Product and BillItem
    code = models.CharField(_("Product code"), max_length=30, blank=False, null=False)
    shortcut = models.CharField(_("Store's internal product number"), max_length=5, blank=False, null=True)
    name = models.CharField(_("Product name"), max_length=50, blank=False, null=False)
    description = models.TextField(_("Product description"), blank=True, null=True)
    private_notes = models.TextField(_("Notes (only for internal use)"), null=True, blank=True)
    unit_type = models.CharField(_("Product unit type"), max_length=15,
        choices=g.UNITS, blank=False, null=False, default=g.UNITS[0][0])
    stock = models.DecimalField(_("Number of items left in stock"),
        max_digits=g.DECIMAL['quantity_digits'],
        decimal_places=g.DECIMAL['quantity_decimal_places'],
        null=False, blank=False)

    # price - in a separate model
    
    class Meta:
        abstract = True


class Product(SkeletonU, ProductAbstract):
    """ these fields will not be copied to BillItem """
    company = models.ForeignKey(Company, null=False, blank=False)
    discounts = models.ManyToManyField(Discount, null=True, blank=True, through='ProductDiscount')
    category = models.ForeignKey(Category, null=True, blank=True)
    # images = models.ManyToManyField(ProductImage, null=True, blank=True) # one image per product is enough
    image = thumbnail.ImageField(_("Icon"),
         upload_to=ImagePath(g.DIRS['product_icon_dir'], "pos_product"),
         null=True, blank=True)
    tax = models.ForeignKey(Tax, null=False, blank=False)
    favorite = models.BooleanField(null=False, default=False)

    def __unicode__(self):
        return self.company.name + ":" + self.name

    ### prices: get and set methods
    def get_price(self):
        """ get product's current base price """
        try:
            return Price.objects.filter(product=self).order_by('-datetime_updated')[0].unit_price
        except:
            return None

    def get_purchase_price(self):
        """ get product's current purchase price """
        try:
            return PurchasePrice.objects.filter(product=self).order_by('-datetime_updated')[0].unit_price
        except:
            return None

    def update_price(self, model, user, new_unit_price):
        """ set a new price for product:
             - if there's no price, just create new
             - if there is a price, update its datetime_updated to now() and create new
               (only if value is different)
             - return current price

             - can be used both for model=Price and model=PurchasePrice
        """
        try:
            old_price = model.objects.get(product=self, datetime_updated=None)
        except model.DoesNotExist:
            old_price = None

        if old_price:
            if old_price.unit_price == new_unit_price:
                # nothing has changed, so do nothing
                return old_price

            # update the old price (datetime_updated will be set)
            try:
                old_price.save()
            except:
                return None

        # create new
        new_price = model(created_by=user,
                          product=self,
                          unit_price=new_unit_price)
        try:
            new_price.save()
        except:
            return None

        return new_price

    ### discounts: get and set methods
    def get_discounts(self):
        """ returns discount objects, ordered by seq_no in intermediate table """
        product_discounts = ProductDiscount.objects.filter(product=self).order_by('seq_no')

        # save discount id and m2m table id
        m2mids = [(x.discount.id, x.id) for x in product_discounts]

        discounts = []
        for i in m2mids: # this is obviously the only way to NOT sort the queryset by 'whatever, not by seq_no'
            # filter out inactive/invalid discounts

            td = Discount.objects.get(id=i[0])
            td.m2mid = i[1]

            if td.is_active:
                discounts.append(td)

        return discounts

    def update_discounts(self, user, discount_ids):
        """ 'smartly' handles ProductDiscount m2m fields with as little repetition/deletion as possible
            discount_ids: list of discount ids (integers) that will have to be on product when this method returns """

        current_discounts_list = self.get_discounts()

        # remove discounts that are not in discount_ids from product,
        for cd in current_discounts_list:
            if cd.id not in discount_ids:
                # this discount must be deleted from product
                ProductDiscount.objects.get(id=cd.m2mid).delete()  # achtung, delete from m2m table, not from discounts!

        # add missing discounts with a valid sequence
        i = 1
        for d in discount_ids:
            try:  # see if this discount exists at all
                discount = Discount.objects.get(company=self.company, id=d)
            except Discount.DoesNotExist:  # there's no such discount in Discount table (why???), don't do anything
                continue

            try:  # see if this discount is already on the product
                m2m = ProductDiscount.objects.get(product=self, discount__id=d)
                modify = True  # modify existing m2m entry
            except ProductDiscount.DoesNotExist:  # it does not exist, add it and assign sequence number
                m2m = ProductDiscount(
                    created_by=user,
                    product=self,
                    discount=discount,
                    seq_no=i
                )
                m2m.save()
                # modification is not required
                modify = False

            if modify:
                m2m.seq_no = i
                m2m.save()

            i += 1

    def add_discount(self, user, discount):
        # add a discount to the end of the list in m2m field;
        seq_no = ProductDiscount.objects.filter(product=self).only('seq_no').order_by('-seq_no')[:0]

        if seq_no:
            seq_no += 1
        else:
            seq_no = 1

        new_discount = ProductDiscount(
            created_by=user,
            product=self,
            discount=discount,
            seq_no=seq_no
        )
        new_discount.save()

    def remove_discount(self, discount):
        try:
            ProductDiscount.objects.get(product=self, discount=discount).delete()
        except ProductDiscount.DoesNotExist:
            return


    @property
    def color(self):
        if self.category:
            return self.category.color
        else:
            return g.CATEGORY_COLORS[0]

    class Meta:
        abstract = False

class ProductDiscount(SkeletonU):
    """ custom many-to-many field for products' discounts: order is important so it must be saved """
    product = models.ForeignKey(Product)
    discount = models.ForeignKey(Discount)
    seq_no = models.IntegerField(_("Order of discount on a product"), null=False)
    
    class Meta:
        ordering = ["seq_no"]  # always order by sequence number
    
    def __unicode__(self):
        return self.product.name + ": " + self.discount.description + ": " + str(self.seq_no)
        

### prices ###
class PriceAbstract(models.Model):
    # used in Price and PurchasePrice
    product = models.ForeignKey(Product)

    def __unicode__(self):
        ret = self.product.name + ": " + str(self.unit_price)

        if self.datetime_updated:
            ret += " (inactive)"

        return ret

    class Meta:
        unique_together = (('product', 'unit_price', 'datetime_updated'),)
        abstract = True

class Price(SkeletonU, PriceAbstract):
    # used for tracking product's price as it changes, but only the last one is displayed
    unit_price = models.DecimalField(_("Price per unit, excluding tax"), max_digits=g.DECIMAL['currency_digits'],
                                     decimal_places=g.DECIMAL['currency_decimal_places'], blank=False, null=False)


### purchase prices ###
class PurchasePrice(SkeletonU, PriceAbstract):
    unit_price = models.DecimalField(_("Purchase price per unit, excluding tax"), max_digits=g.DECIMAL['currency_digits'],
                                     decimal_places=g.DECIMAL['currency_decimal_places'], blank=False, null=False)


### contacts ###
class ContactAbstract(models.Model):
    # used for Contact and BillContact
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
    vat = models.CharField(_("VAT identification number"), max_length=30, null=True, blank=True)

    @property
    def country_name(self):
        return country_by_code.get(self.country)

    def __unicode__(self):
        if self.type == "Individual":
            return "Individual: " + self.first_name + " " + self.last_name
        else:
            return "Company: " + str(self.company_name)

    class Meta:
        abstract = True


class Contact(SkeletonU, ContactAbstract):
    company = models.ForeignKey(Company)


### permissions
class Permission(SkeletonU):
    user = models.ForeignKey(BlocklogicUser)
    company = models.ForeignKey(Company)
    permission = models.CharField(max_length=16, null=False, blank=False, choices=g.PERMISSION_GROUPS)
    pin = models.IntegerField(null=True)

    unique_together = ('company', 'pin')

    def __unicode__(self):
        return self.user.email + " | " + self.company.name + ": " + self.get_permission_display()

    def create_pin(self, custom_pin=None, save=True):
        """ creates a pin for this user; if successful, returns True;
            if this pin already exists in current company, returns False
        """
        def rnd_pin():
            return random.randint(0, 10**g.PIN_LENGTH)

        def pin_exists(this_pin):
            # exclude this permission from checking;
            return Permission.objects.filter(company=self.company, pin=this_pin).exclude(id=self.id).exists()

        if custom_pin:
            if pin_exists(custom_pin):
                return False

            p = custom_pin
        else:
            p = rnd_pin()
            while pin_exists(p):
                p = rnd_pin()

        self.pin = p

        if save:
            self.save()

        return True


    @property
    def pin_display(self):
        return "%04d"%(self.pin % 10000)


@receiver(pre_save, sender=Permission)
@receiver(pre_delete, sender=Permission)
def delete_permission_cache(**kwargs):
    """ deletes cached permissions on save or delete """
    from common.functions import permission_cache_key
    from django.core.cache import cache
    
    ckey = permission_cache_key(kwargs['instance'].user, kwargs['instance'].company)
    cache.delete(ckey)


### register (till) ###
class RegisterAbstract(models.Model):
    name = models.CharField(_("Name of cash register"), max_length=50, null=False, blank=False)
    receipt_format = models.CharField(_("Receipt format"), max_length=32, choices=g.RECEIPT_FORMATS, null=False,
                                      blank=False)
    receipt_type = models.CharField(_("Receipt type"), max_length=32, choices=g.RECEIPT_TYPES, null=False)
    print_logo = models.BooleanField(_("Print logo on thermal receipts"), blank=False, default=True)
    location = models.TextField(_("Location of this register"), max_length=120, null=True, blank=True)
    print_location = models.BooleanField(_("Print location of register"), blank=False, default=True)

    class Meta:
        abstract = True


class Register(SkeletonU, RegisterAbstract):
    company = models.ForeignKey(Company, null=False, blank=False)
    printer_driver = models.CharField(_("Printer driver"), max_length=50, null=False, choices=g.PRINTER_DRIVERS)
    device_id = models.CharField(_("Device id"), max_length=128, null=True, blank=True)


### bill details ###
class BillCompany(SkeletonU, CompanyAbstract):
    # details about the company that issued <this> bill;
    # this is obviously the current company the user's working in
    company = models.ForeignKey(Company, null=False, blank=False)


class BillContact(SkeletonU, ContactAbstract):
    # stuff from  contact: inherited from ContactAbstract
    contact = models.ForeignKey(Contact, null=False, blank=False)


class BillRegister(SkeletonU, RegisterAbstract):
    # stuff from the register that <this> bill was 'printed' on: inherit from RegisterAbstract
    register = models.ForeignKey(Register, null=False, blank=False)


class Bill(SkeletonU, RegisterAbstract):
    # inherited fields from: RegisterAbstract, ContactAbstract,
    company = models.ForeignKey(Company, null=False, blank=False)  # also an issuer of the bill

    # every time a bill is created, copy the data that has changed since the last bill was saved to history.
    issuer = models.ForeignKey(BillCompany)  # when company data hasn't changed, this is equal to Bill.company
    contact = models.ForeignKey(BillContact, null=True)
    register = models.ForeignKey(BillRegister, null=False)

    # save user's id as an integer (not as a foreign key) and user name as well in case that user gets deleted
    user_id = models.IntegerField(null=False)
    user_name = models.CharField(max_length=64, null=False)

    serial = models.IntegerField(_("Bill number, unique over all company's bills"), null=True)  # will be updated in post_save signal

    # discount applied to whole bill
    discount_amount = models.DecimalField(_("Discount on the whole bill (absolute or relative)"),
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=True, blank=True)

    discount_type = models.CharField(_("Type of discount"),
        max_length=16,
        choices=g.DISCOUNT_TYPES,
        null=True, blank=True)

    ### PRICES:
    base = models.DecimalField(_("Sub total"),  # all items' batch prices
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=True, blank=True)

    discount = models.DecimalField(_("Discount, sum of all discounts"),  # all items' batch prices
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=True, blank=True)

    tax = models.DecimalField(_("Tax amount, absolute value, sum of all items' taxes"),
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=True, blank=True)

    notes = models.CharField(_("Notes"), max_length=1000, null=True, blank=True)

    payment = models.ForeignKey('payment.Payment', null=True, blank=True)

    # this field should be the same value as in payment.status (except when someone paid, and the storno)
    # status = models.CharField(_("Bill status"), max_length=20, choices=g.BILL_STATUS, default=g.BILL_STATUS[0][0])

    timestamp = models.DateTimeField(_("Date and time of bill creation"), null=False)

    def __unicode__(self):
        return self.company.name + ": " + str(self.serial)

    @property
    def currency(self):
        return self.payment.currency

    @currency.setter
    def currency(self, value):
        from payment.models import Payment

        try:
            payment = Payment.objects.get(id=self.payment)
            payment.currency = value
            payment.save()
        except Payment.DoesNotExist:
            pass

    @property
    def total(self):
        """
        total of bill and payment is the same for now, maybe in the future we
        will have to change it, but for now, porn
        """""
        return self.payment.total

    @total.setter
    def total(self, value):
        from payment.models import Payment

        try:
            payment = Payment.objects.get(id=self.payment)
            payment.total = value
            payment.save()
        except Payment.DoesNotExist:
            pass

    @property
    def status(self):
        """
        status of bill and payment is the same for now, maybe in the future we
        will have to change it, but for now it suffice.

        returns status of bill and payment
        """
        return self.payment.status

    @status.setter
    def status(self, value):
        from payment.models import Payment

        """
        sets status of bill and payment
        """
        try:
            payment = self.payment
            payment.status = value
            payment.save()
        except Payment.DoesNotExist:
            pass

# pre-save signal: set bill's serial number
@receiver(pre_save, sender=Bill)
def set_serial(instance, **kwargs):
    # set serial number after the bill has been paid;
    if not instance.serial:
        try:
            # get the second last bill (because the last is this bill without serial)
            last_bill = Bill.objects.only('serial') \
                            .filter(company=instance.company) \
                            .exclude(serial=None) \
                            .order_by('-serial')[0]
            instance.serial = last_bill.serial + 1
            instance.timestamp = dtm.datetime.utcnow()
        except:
            instance.serial = 1


class BillItem(SkeletonU, ProductAbstract): # include all data from Product
    bill = models.ForeignKey(Bill)
    product_id = models.BigIntegerField(null=False)  # stor reference to product (used by UI/jQuery/stats/...)
                                                     # (not a FK, in case the product gets deleted)

    bill_notes = models.CharField(_("Bill notes"),
        help_text=_("Notes for this item, shown on bill (like expiration date or serial number)"),
        max_length=1000, null=True, blank=True)

    ### PRICES: ###
    #   values for single item:
    #     base: price for quantity = 1
    #     quantity
    #     tax_rate: tax in percent
    base = models.DecimalField(_("Base price (for single item), without tax and discounts"),
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=False, blank=False)

    quantity = models.DecimalField(_("Quantity"),
        max_digits=g.DECIMAL['quantity_digits'],
        decimal_places=g.DECIMAL['quantity_decimal_places'],
        null=False, blank=False)

    tax_rate = models.DecimalField(_("Tax in percent, copied from product's tax rate"),
        max_digits=g.DECIMAL['percentage_decimal_places']+3,
        decimal_places=g.DECIMAL['percentage_decimal_places'],
        null=True, blank=True)

    # values for item as will be shown on bill:
    #     batch: single_base * quantity
    #     discount: absolute amount of discount on this item
    #     net: base - discounts
    #     tax: absolute value of tax
    #     total: base - discounts + tax
    batch = models.DecimalField(_("Base price, multiplied by quantity"),
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=False, blank=False)

    discount = models.DecimalField(_("Discount, absolute value, sum of all valid discounts on this item"),
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=True, blank=True)

    net = models.DecimalField(_("Base price minus discounts"),
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=False, blank=False)

    tax = models.DecimalField(_("Tax amount, absolute value"),
        max_digits=g.DECIMAL['currency_digits'],
        decimal_places=g.DECIMAL['currency_decimal_places'],
        null=False, blank=False)

    total = models.DecimalField(_("Total price, including taxes, discounts and multiplied by quantity"),
        max_digits=g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
        null=False, blank=False)

    def __unicode__(self):
        return str(self.bill.id) + ": " + self.name


### item's discounts
class BillItemDiscount(SkeletonU, DiscountAbstract):
    # inherits everything from DiscountAbstract
    bill_item = models.ForeignKey(BillItem)


### track changes:
# company
@receiver(post_save, sender=Company)
def company_updated(instance, **kwargs):
    from common.functions import compare_objects, copy_data

    # get the last saved object from that table and see if anything has changed
    last_object = BillCompany.objects.filter(company=instance).order_by('-datetime_created')[:1]

    if len(last_object) > 0:
        last_object = last_object[0]
        if compare_objects(last_object, instance) is True:
            # there are no changes, there's nothing to be done
            return

    # something has changed, create a new copy of instance in model
    # create a new BillCompany
    bill_company = BillCompany(
        created_by=instance.created_by,
        company=instance
    )

    copy_data(instance, bill_company)
    bill_company.save()


# register
@receiver(post_save, sender=Register)
def register_updated(instance, **kwargs):  # see comments for company_updated
    from common.functions import compare_objects, copy_data

    last_object = BillRegister.objects.filter(register=instance).order_by('-datetime_updated')[:1]

    if len(last_object) > 0:
        last_object = last_object[0]
        if compare_objects(last_object, instance) is True:
            return

    bill_register = BillRegister(
        created_by=instance.created_by,
        register=instance
    )
    copy_data(instance, bill_register)
    bill_register.save()


# contact
@receiver(post_save, sender=Contact)
def contact_updated(instance, **kwargs):
    from common.functions import compare_objects, copy_data

    last_object = BillContact.objects.filter(contact=instance).order_by('-datetime_updated')[:1]

    if len(last_object) > 0:
        last_object = last_object[0]
        if compare_objects(last_object, instance) is True:
            return

    bill_contact = BillContact(
        contact=instance,
        created_by=instance.created_by
    )
    copy_data(instance, bill_contact)
    bill_contact.save()


### synchonization
def signal_change(instance, created, action, **kwargs):
    from sync.models import Sync
    if not instance.company:
        return

    sync_objects = Sync.objects.only('seq')\
        .filter(company=instance.company).order_by('-seq')

    last_key = 0

    if len(sync_objects) > 0:
        last_key = sync_objects[0].seq

    try:
        object = Sync.objects.get(company=instance.company, object_id=instance.id, model=instance.__class__.__name__)
        object.seq = last_key+1
        object.action = action
        object.save()
    except Sync.DoesNotExist:
        sync = Sync(company=instance.company,
                    action=action,
                    model=instance.__class__.__name__,
                    object_id=instance.id,
                    seq=last_key+1)
        sync.save()


@receiver(post_delete, sender=Category)
@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=Contact)
@receiver(post_delete, sender=Tax)
@receiver(post_delete, sender=Discount)
@receiver(post_delete, sender=Register)
def set_serial_delete(instance, **kwargs):
    signal_change(instance, False, action='delete', **kwargs)


@receiver(post_save, sender=Category)
@receiver(post_save, sender=Product)
@receiver(post_save, sender=Contact)
@receiver(post_save, sender=Tax)
@receiver(post_save, sender=Discount)
@receiver(post_save, sender=Register)
def set_serial_save(instance, created, **kwargs):
    signal_change(instance, created, action='save', **kwargs)

