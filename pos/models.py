from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from sorl import thumbnail

from common.models import SkeletonU
from common.functions import ImagePath
import common.globals as g

from config.countries import country_choices, country_by_code

import datetime as dtm
import json


### company ###
class Company(SkeletonU):
    name = models.CharField(_("Company name"), max_length=200, null=False, blank=False)
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
    street = models.CharField(_("Street and house number"), max_length=200, null=True, blank=True)
    postcode = models.CharField(_("Postal code"), max_length=20, null=True, blank=True)
    city = models.CharField(_("City"), max_length=50, null=True, blank=True)
    state = models.CharField(_("State"), max_length=50, null=True, blank=True)
    country = models.CharField(max_length=2,  choices=country_choices, null=True, blank=True)
    email = models.CharField(_("E-mail address"), max_length=256, null=False, blank=False)
    website = models.CharField(_("Website"), max_length=256, null=True, blank=True)
    phone = models.CharField(_("Phone number"), max_length=30, null=True, blank=True)
    vat_no = models.CharField(_("VAT exemption number"), max_length=30, null=False, blank=False)
    notes = models.TextField(_("Notes"), blank=True, null=True)

    def __unicode__(self):
        return self.name

    @property
    def country_name(self):
        return country_by_code.get(self.country)

    class Meta:
        verbose_name_plural = _("Companies")


# not in use at the moment
#class CompanyAttribute(SkeletonU):
#    company = models.ForeignKey(Company)
#    attribute_name = models.CharField(_("Attribute name"), max_length=g.ATTR_LEN['name'], null=False, blank=False)
#    attribute_value = models.CharField(_("Attribute value"), max_length=g.ATTR_LEN['value'], null=False, blank=False)
#    
#    def __unicode__(self):
#        return self.company.name + ": " + self.attribute_name + " = " + self.attribute_value


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



# not in use at the moment
#class CategoryAttribute(SkeletonU):
#    category = models.ForeignKey(Category)
#    attribute_name = models.CharField(_("Attribute name"), max_length=g.ATTR_LEN['name'], null=False, blank=False)
#    attribute_value = models.CharField(_("Attribute value"), max_length=g.ATTR_LEN['value'], null=False, blank=False)
#    
#    def __unicode(self):
#        return self.category.name + ": " + self.attribute_name + " = " + self.attribute_value


### discounts ###
class DiscountAbstract(SkeletonU):
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


class Discount(DiscountAbstract):
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

### product ###
# for now, one image per product is enough (web pos != web store)
#class ProductImage(SkeletonU):
#    description = models.TextField(_('Image description'), blank=True, null=True)
#    image = models.ImageField(upload_to=get_image_path(g.DIRS['product_image_dir'], "pos_productimage"), null=False)
#    original_filename = models.CharField(_('Original filename'), max_length=255, blank=True, null=True)


class ProductAbstract(SkeletonU):
    """ all these fields will be copied to BillItem """
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


class Product(ProductAbstract):
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

# not in use at the moment
#class ProductAttribute(SkeletonU): # currently not in plan
#    product = models.ForeignKey(Product, null=False, blank=False)
#    attribute_name = models.CharField(_("Attribute name"), max_length=g.ATTR_LEN['name'], null=False, blank=False)
#    attribute_value = models.CharField(_("Attribute value"), max_length=g.ATTR_LEN['value'], null=False, blank=False)


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
class Price(SkeletonU):
    product = models.ForeignKey(Product)
    unit_price = models.DecimalField(_("Price per unit, excluding tax"), max_digits=g.DECIMAL['currency_digits'],
                                     decimal_places=g.DECIMAL['currency_decimal_places'], blank=False, null=False)
    # use Skeleton.datetime_updated() instead of this: (the same functionality)
    # date_updated = models.DateTimeField(blank=True, null=True) # determines whether that's the current price for product (if this field is empty)
    
    def __unicode__(self):
        ret = self.product.name + ": " + str(self.unit_price)

        if self.datetime_updated:
            ret += " (inactive)"

        return ret
    
    class Meta:
        unique_together = (('product', 'unit_price', 'datetime_updated'),)


### purchase prices ###
class PurchasePrice(SkeletonU):
    product = models.ForeignKey(Product)
    unit_price = models.DecimalField(_("Purchase price per unit, excluding tax"), max_digits=g.DECIMAL['currency_digits'],
                                     decimal_places=g.DECIMAL['currency_decimal_places'], blank=False, null=False)
    
    def __unicode__(self):
        ret = self.product.name + ": " + str(self.unit_price)

        if self.datetime_updated:
            ret += " (inactive)"

        return ret
    
    class Meta:
        unique_together = (('product', 'unit_price', 'datetime_updated'),)


### contacts ###
class Contact(SkeletonU):
    company = models.ForeignKey(Company)
    type = models.CharField(_("Type of contact"), max_length=20, choices=g.CONTACT_TYPES, null=False, blank=False, default=g.CONTACT_TYPES[0][0])
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
    
    def __unicode__(self):
        if self.type == "Individual":
            return "Individual: " + self.first_name + " " + self.last_name
        else:
            return "Company: " + str(self.company_name)

    @property
    def country_name(self):
        return country_by_code.get(self.country)

# not in use at the moment   
#class ContactAttribute(SkeletonU):
#    contact = models.ForeignKey(Contact)
#    attribute_name = models.CharField(_("Attribute name"), max_length=g.ATTR_LEN['name'], null=False, blank=False)
#    attribute_value = models.CharField(_("Attribute value"), max_length=g.ATTR_LEN['value'], null=False, blank=False)
#    
#    def __unicode__(self):
#        return str(self.contact) + ": " + self.attribute_name + " = " + self.attribute_value


### permissions
class Permission(SkeletonU):
    user = models.ForeignKey(User)
    company = models.ForeignKey(Company)
    permission = models.CharField(max_length=16, null=False, blank=False, choices=g.PERMISSION_GROUPS)
    
    def __unicode__(self):
        return self.user.email + " | " + self.company.name + ": " + self.get_permission_display()


@receiver(pre_save, sender=Permission)
@receiver(pre_delete, sender=Permission)
def delete_permission_cache(**kwargs):
    """ deletes cached permissions on save or delete """
    from views.util import permission_cache_key
    from django.core.cache import cache
    
    ckey = permission_cache_key(kwargs['instance'].user, kwargs['instance'].company)
    cache.delete(ckey)


### register (till) ###
class Register(SkeletonU):
    company = models.ForeignKey(Company, null=False, blank=False)
    # each company must have at least one register; each register carries the following settings
    name = models.CharField(_("Name of cash register"), max_length=50, null=False, blank=False)
    printer_driver = models.CharField(_("Printer driver"), max_length=50, null=False, choices=g.PRINTER_DRIVERS)
    receipt_format = models.CharField(_("Receipt format"), max_length=32, choices=g.RECEIPT_FORMATS, null=False, blank=False)
    receipt_type = models.CharField(_("Receipt type"), max_length=32, choices=g.RECEIPT_TYPES, null=False)
    print_logo = models.BooleanField(_("Print logo on thermal receipts"), blank=False, default=True)

    location = models.TextField(_("Location of this register"), max_length=120, null=True, blank=True)
    print_location = models.BooleanField(_("Print location of register"), blank=False, default=True)

    #print_settings = models.TextField(_("Printer settings"), null=True, blank=True)


### bills ###
class Bill(SkeletonU):
    company = models.ForeignKey(Company, null=False, blank=False)  # also an issuer of the bill
    user = models.ForeignKey(User, null=False)
    till = models.ForeignKey(Register, null=False, blank=False)
    serial = models.IntegerField(_("Bill number, unique over all company's bills"), null=True)  # will be updated in post_save signal

    type = models.CharField(_("Bill type"), max_length=20, choices=g.BILL_TYPES, null=False, blank=False, default=g.BILL_TYPES[0][0])
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='bill_recipient_company')
    note = models.CharField(_("Notes"), max_length=1000, null=True, blank=True)
    sub_total = models.DecimalField(_("Sub total"),
                                    max_digits=g.DECIMAL['currency_digits'],
                                    decimal_places=g.DECIMAL['currency_decimal_places'],
                                    null=True, blank=True)

    # discount on the whole bill
    discount = models.DecimalField(_("Discount on the whole bill (absolute or percent)"),
                                   max_digits=g.DECIMAL['currency_digits'],
                                   decimal_places=g.DECIMAL['currency_decimal_places'],
                                   null=True, blank=True)
    discount_type = models.CharField(_("Type of discount"),
                                     max_length=16,
                                     choices=g.DISCOUNT_TYPES,
                                     null=True, blank=True)

    tax = models.DecimalField(_("Tax amount, absolute value, derived from products"), 
                              max_digits=g.DECIMAL['currency_digits'],
                              decimal_places=g.DECIMAL['currency_decimal_places'],
                              null=True, blank=True)
    total = models.DecimalField(_("Total amount to be paid"), 
                                max_digits=g.DECIMAL['currency_digits'],
                                decimal_places=g.DECIMAL['currency_decimal_places'],
                                null=True, blank=True)

    # payment type and reference: this will be updated after the bill is saved
    payment_type = models.CharField(_("Payment type"), max_length=32, choices=g.PAYMENT_TYPES, null=True, blank=True)
    payment_reference = models.TextField(_("Payment reference"), null=True, blank=True)

    timestamp = models.DateTimeField(_("Date and time of bill creation"), null=False)
    due_date = models.DateTimeField(_("Due date"), null=True)
    status = models.CharField(_("Bill status"), max_length=20, choices=g.BILL_STATUS, default=g.BILL_STATUS[0][0])
    
    def __unicode__(self):
        return self.company.name + ": " + str(self.serial)
    
    #def save(self):
    #    super(Bill, self).save()
    #    copy_bill_to_history(self.id) # always put a copy in history


# post-save signal: set bill's serial number
@receiver(post_save, sender=Bill)
def set_serial(instance, created, **kwargs):
    if not created:  # only set the serial number once
        return

    if not instance.company:
        return

    try:
        # get the second last bill (because the last is this bill without serial)
        last_bill = Bill.objects.only('serial') \
                        .filter(company=instance.company) \
                        .exclude(serial=None) \
                        .order_by('-serial')[0]
        instance.serial = last_bill.serial + 1
    except:
        instance.serial = 1

    instance.save()


class BillItem(ProductAbstract): # include all data from Product
    bill = models.ForeignKey(Bill)
    product_id = models.BigIntegerField(null=False) # store reference to product (used by UI/jQuery/...)
    quantity = models.DecimalField(_("Quantity"), max_digits = g.DECIMAL['quantity_digits'],
                                  decimal_places = g.DECIMAL['quantity_decimal_places'],
                                  null=False, blank=False)
    base_price = models.DecimalField(_("Base price"), # hard-coded price from current Price table
                                     max_digits = g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                     null=False, blank=False)
    tax_percent = models.DecimalField(_("Tax in percent, copied from product's tax rate"), 
                                      max_digits = g.DECIMAL['percentage_decimal_places']+3, decimal_places=g.DECIMAL['percentage_decimal_places'],
                                      null=True, blank=True)
    tax_absolute = models.DecimalField(_("Tax amount (absolute value)"), # hard-coded price from current Price table
                                       max_digits = g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                       null=False, blank=False)
    discount_absolute = models.DecimalField(_("Discount, absolute value, sum of all valid discounts on this product"), 
                                            max_digits = g.DECIMAL['currency_digits'],
                                            decimal_places=g.DECIMAL['currency_decimal_places'], null=True, blank=True)
    single_total = models.DecimalField(_("Total price for a single item"),
                                       max_digits = g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                       null=False, blank=False)
    total = models.DecimalField(_("Total price"),
                                max_digits = g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                null=False, blank=False)
    
    bill_notes = models.CharField(_("Bill notes"), max_length=1000, null=True, blank=True,
                                  help_text=_("Notes for this item, shown on bill (like expiration date or serial number)"))
    
    def __unicode__(self):
        return str(self.bill.id) + ": " + self.name
    
    #def save(self):
    #    super(BillItem, self).save()
    #    copy_bill_to_history(self.bill.id) # always put a copy in history


### item's discounts
class BillItemDiscount(DiscountAbstract):
    # inherits everything from DiscountAbstract
    bill_item = models.ForeignKey(BillItem)


### history
class BillHistory(SkeletonU):
    bill = models.ForeignKey(Bill)
    data = models.TextField(_("Serialized Bill history"), null=False)
    
    class Meta:
        verbose_name_plural = _("Bill history")


def model_to_dict(obj, ignore=None, exclude=None):
    """ converts django model object to dictionary.
        ignores data that is in ignore list.
        includes data from foreign key objects, if it's not in exclude[] list.
        ignore takes precedence over exclude. """
    if not obj:
        return ''

    if ignore is None:
        ignore = []
    if exclude is None:
        exclude = []
    
    data = {}
    
    # put all fields' values in a dictionary
    for field in obj._meta.fields:
        if field.name in ignore: # don't touch
            continue
        
        if field.rel: # if this is a foreign key, write down the whole object
            sub_obj = getattr(obj, str(field.name))
            if str(field.name) not in exclude: # if include, then copy FK data
                data[str(field.name)] = model_to_dict(sub_obj, ignore=ignore, exclude=exclude)
            else: # otherwise, just use the __unicode__ method, defined in the model
                data[str(field.name)] = unicode(sub_obj)
        else:
            key = str(field.name)
            value = getattr(obj, str(field.name))
            # for taking care of specific fields
            #datatype = field.get_internal_type()
            if not value:
                value = ''
            
            data[key] = unicode(value)

    return data


def copy_bill_to_history(bill_id):
    """ serializes Bill, BillItem and all foreign-keyed tables,
        puts them in JSON format and saves to BillHistory. """
    
    data = {}
    
    ignore_list = ['image']
    exclude_list = ['created_by', 'updated_by']
    b = Bill.objects.get(id=bill_id)
    
    # about the bill
    data['bill'] = model_to_dict(b, ignore=ignore_list, exclude=exclude_list)
    
    # about the items
    data['items'] = []
    
    i = BillItem.objects.filter(bill__id=bill_id)
    exclude_list.append('bill') # bill is already in "bill"
    
    for item in i:
        data['items'].append(model_to_dict(item, ignore=ignore_list, exclude=exclude_list))
    
    serialized_data = json.dumps(data)
    
    history = BillHistory(created_by=b.created_by,
                          bill=b, data=serialized_data)
    history.save()
    return True




@receiver(post_delete, sender=Category)
@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=Contact)
@receiver(post_delete, sender=Tax)
@receiver(post_delete, sender=Discount)
def set_serial_delete(instance, **kwargs):
    signal_change(instance, False, action='delete', **kwargs)
# author: Android lord


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

@receiver(post_save, sender=Category)
@receiver(post_save, sender=Product)
@receiver(post_save, sender=Contact)
@receiver(post_save, sender=Tax)
@receiver(post_save, sender=Discount)
def set_serial_save(instance, created, **kwargs):
    signal_change(instance, created, action='save', **kwargs)

