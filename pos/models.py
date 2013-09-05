from django.db import models
from django.utils.translation import ugettext as _
from django.db.models.signals import pre_save # image file cleanup signals
from django.dispatch import receiver
from config.models import Cleanup

from common.models import SkeletonU
from common.functions import get_image_path
import common.globals as g

from config.models import Country

from datetime import datetime
import json

### company ###
class Company(SkeletonU):
    name = models.CharField(_("Company name"), max_length=200, null=False, blank=False)
    url_name = models.SlugField(_("Company name, used in URL address"),
                                max_length=g.MISC['company_url_length'],
                                null=False, blank=False, db_index=True)
    image = models.ImageField(_("Logo"),
                             upload_to=get_image_path(g.DIRS['logo_dir'], "pos_company"),
                             null=True, blank=True)
    street = models.CharField(_("Street and house number"), max_length=200, null=True, blank=True)
    postcode = models.CharField(_("Postal code"), max_length=20, null=True, blank=True)
    city = models.CharField(_("City"), max_length=50, null=True, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True)
    email = models.CharField(_("E-mail address"), max_length=256, null=False, blank=False)
    website = models.CharField(_("Website"), max_length=256, null=True, blank=True)
    phone = models.CharField(_("Phone number"), max_length = 30, null=True, blank=True)
    vat_no = models.CharField(_("VAT exemption number"), max_length=30, null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = _("Companies")

class CompanyAttribute(SkeletonU):
    company = models.ForeignKey(Company)
    attribute_name = models.CharField(_("Attribute name"), max_length=g.ATTR_LEN['name'], null=False, blank=False)
    attribute_value = models.CharField(_("Attribute value"), max_length=g.ATTR_LEN['value'], null=False, blank=False)
    
    def __unicode__(self):
        return self.company.name + ": " + self.attribute_name + " = " + self.attribute_value
    
### category ###
class Category(SkeletonU):
    company = models.ForeignKey(Company, null=False, blank=False)
    parent = models.ForeignKey('self', blank=True, null=True)
    name = models.CharField(_("Category name"), max_length=100, null=False, blank=False)
    description = models.TextField(_("Description"), null=True, blank=True)
    image = models.ImageField(_("Icon"),
                             upload_to=get_image_path(g.DIRS['category_icon_dir'], "pos_category"),
                             null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = _("Categories")

class CategoryAttribute(SkeletonU):
    category = models.ForeignKey(Category)
    attribute_name = models.CharField(_("Attribute name"), max_length=g.ATTR_LEN['name'], null=False, blank=False)
    attribute_value = models.CharField(_("Attribute value"), max_length=g.ATTR_LEN['value'], null=False, blank=False)
    
    def __unicode(self):
        return self.category.name + ": " + self.attribute_name + " = " + self.attribute_value

### discounts ### 
class Discount(SkeletonU):
    company = models.ForeignKey(Company)
    description = models.TextField(_("Discount description"), null=True, blank=True)
    code = models.CharField(_("Discount code"), max_length=50, null=True, blank=True)
    type = models.CharField(_("Discount type"), max_length=30, choices=g.DISCOUNT_TYPES, null=False, blank=False, default=g.DISCOUNT_TYPES[0][0])
    amount = models.DecimalField(_("Discount amount"),
                                 max_digits=g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                 null=False, blank=False)
    start_date = models.DateField(_("Discount start date"), null=True, blank=True)
    end_date = models.DateField(_("Discount end date"), null=True, blank=True)
    active = models.BooleanField(_("Active"), null=False, blank=True, default=True)
    
    def __unicode__(self):
        return self.code + " " + self.description

### product ###
class ProductImage(SkeletonU):
    description = models.TextField(_('Image description'), blank=True, null=True)
    image = models.ImageField(upload_to=get_image_path(g.DIRS['product_image_dir'], "pos_productimage"), null=False)
    original_filename = models.CharField(_('Original filename'), max_length=255, blank=True, null=True)

class ProductAbstract(SkeletonU):
    """ used for product and bill item """
    code = models.CharField(_("Product code"), max_length=30, blank=True, null=True)
    shop_code = models.IntegerField(_("Store's internal product number"), blank=False, null=False)
    name = models.CharField(_("Product name"), max_length=50, blank=False, null=False)
    description = models.TextField(_("Product description"), blank=True, null=True)
    private_notes = models.TextField(_("Notes (only for internal use)"), null=True, blank=True)
    unit_type = models.CharField(_("Product unit type"), max_length=15,
                                    choices = g.UNITS, blank=False, null=False, default=g.UNITS[0][0])
    # price is in a separate model
    tax = models.DecimalField(_("Tax amount"), max_digits=g.DECIMAL['percentage_decimal_places']+3,
                              decimal_places=g.DECIMAL['percentage_decimal_places'], null=False, blank=False)
    
    class Meta:
        abstract = True

class Product(ProductAbstract):
    # foreign keys, changed data in Company/Discount/... will be reflected in Product and BillItem
    company = models.ForeignKey(Company, null=False, blank=False)
    discount = models.ManyToManyField(Discount, null=True, blank=True)
    category = models.ForeignKey(Category, null=True, blank=True)
    stock = models.IntegerField(_("Number of items left in stock"), null=True, blank=True)
    image = models.ImageField(_("Icon"),
                             upload_to=get_image_path(g.DIRS['product_icon_dir'], "pos_productimage"),
                             null=True, blank=True)
    images = models.ManyToManyField(ProductImage, null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        abstract = False

class ProductAttribute(SkeletonU): # currently not in plan
    product = models.ForeignKey(Product, null=False, blank=False)
    attribute_name = models.CharField(_("Attribute name"), max_length=g.ATTR_LEN['name'], null=False, blank=False)
    attribute_value = models.CharField(_("Attribute value"), max_length=g.ATTR_LEN['value'], null=False, blank=False)

### prices ###
class Price(SkeletonU):
    product = models.ForeignKey(Product)
    unit_price = models.DecimalField(_("Price per unit, excluding tax"), max_digits=g.DECIMAL['currency_digits'],
                                     decimal_places=g.DECIMAL['currency_decimal_places'], blank=False, null=False)
    date_updated = models.DateTimeField(blank=True, null=True) # determines whether that's the current price for product (if this field is empty)
    
    def __unicode__(self):
        ret = self.product.name + ": " + str(self.unit_price)

        if not self.date_updated:
            ret += " (inactive)"

        return ret
    
    def save(self, plain_save=False):
        """ if the price has changed, set the old one's date and write a new entry """
        """ also save if there's no need for any of the below logic """
        if self.pk is None or plain_save is True:
            super(Price, self).save()
        else:
            # find the last price of product
            last_price = Price.objects.get(id=self.id)
            last_price.date_updated = datetime.now()
            last_price.save(plain_save = True)
            
            new_price = Price(created_by = last_price.created_by, 
                              product = self.product, unit_price = self.unit_price)
            new_price.save(plain_save = True)
            
### contacts ###
class Contact(SkeletonU):
    company = models.ForeignKey(Company)
    type = models.CharField(_("Type of contact"), max_length=20, choices=g.CONTACT_TYPES, null=False, blank=False, default=g.CONTACT_TYPES[0][0])
    company_name = models.CharField(_("Company name"), max_length=50, null=True, blank=True)
    first_name = models.CharField(_("First name"), max_length=50, null=True, blank=True)
    last_name = models.CharField(_("Last name"), max_length=50, null=True, blank=True)
    date_of_birth = models.DateField(_("Date of birth"), null=True, blank=True)
    street_address = models.CharField(_("Street and house number"), max_length=200, null=True, blank=True)
    postcode = models.CharField(_("Post code/ZIP"), max_length=12, null=True, blank=True)
    city = models.CharField(_("City"), max_length=50, null=True, blank=True)
    country = models.ForeignKey(Country) 
    email = models.CharField(_("E-mail address"), max_length=255, blank=False, null=False)
    phone = models.CharField(_("Telephone number"), max_length=30, blank=True, null=True)
    vat = models.CharField(_("VAT identification number"), max_length=30, null=True, blank=True)
    
    def __unicode__(self):
        if type == "Individual":
            return "Individual: " + self.first_name + " " + self.last_name
        else:
            return "Company: " + self.company_name
    
class ContactAttribute(SkeletonU):
    contact = models.ForeignKey(Contact)
    attribute_name = models.CharField(_("Attribute name"), max_length=g.ATTR_LEN['name'], null=False, blank=False)
    attribute_value = models.CharField(_("Attribute value"), max_length=g.ATTR_LEN['value'], null=False, blank=False)
    
    def __unicode(self):
        return str(self.contact) + ": " + self.attribute_name + " = " + self.attribute_value

### bills ###
class Bill(SkeletonU):
    company = models.ForeignKey(Company, null=False, blank=False) # also an issuer of the bill
    type = models.CharField(_("Bill type"), max_length=20, choices=g.BILL_TYPES, null=False, blank=False, default=g.BILL_TYPES[0][0])
    recipient_company = models.ForeignKey(Company, null=True, blank=True, related_name='bill_recipient_company')
    recipient_contact = models.ForeignKey(Contact, null=True, blank=True) 
    note = models.CharField(_("Notes"), max_length=1000, null=True, blank=True)
    sub_total = models.DecimalField(_("Sub total"),
                                    max_digits = g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                    null=False, blank=False)
    discount = models.DecimalField(_("Discount on the whole bill, in percentage"), 
                                   max_digits = g.DECIMAL['percentage_decimal_places']+3, decimal_places=g.DECIMAL['percentage_decimal_places'],
                                   null=True, blank=True)
    tax = models.DecimalField(_("Tax amount, absolute value, derived from products"), 
                                   max_digits = g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                   null=True, blank=True)
    timestamp = models.DateTimeField(_("Date and time of bill creation"), auto_now_add=True)
    status = models.CharField(_("Bill status"), max_length=20, choices=g.BILL_STATUS, default=g.BILL_STATUS[0][0])
    
    def __unicode__(self):
        return self.company.name + ": " + str(self.sub_total)
    
    def save(self):
        super(Bill, self).save()
        copy_bill_to_history(self.id) # always put a copy in history

class BillItem(ProductAbstract): # include all data from Product
    bill = models.ForeignKey(Bill)
    quantity = models.DecimalField(_("Quantity"), max_digits = g.DECIMAL['quantity_digits'],
                                 decimal_places = g.DECIMAL['quantity_decimal_places'],
                                 null=False, blank=False)
    price = models.DecimalField(_("Sub total"), # hard-coded price from current Price table
                                max_digits = g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                null=False, blank=False)
    discount_sum = models.DecimalField(_("Discount, absolute value, sum of all current discounts"), 
                                   max_digits = g.DECIMAL['currency_digits'], decimal_places=g.DECIMAL['currency_decimal_places'],
                                   null=True, blank=True)
    bill_notes = models.CharField(_("Bill notes") ,max_length=1000, null=True, blank=True,
                                  help_text=_("Notes shown on bill, like expiration date or serial number"))
    
    def __unicode__(self):
        return str(self.bill.id) + ": " + self.name
    
    def save(self):
        super(BillItem, self).save()
        copy_bill_to_history(self.bill.id) # always put a copy in history

### history
class BillHistory(SkeletonU):
    bill = models.ForeignKey(Bill)
    data = models.TextField(_("Serialized Bill history"), null=False)
    
    class Meta:
        verbose_name_plural = _("Bill history")

def model_to_dict(obj, ignore=[], exclude=[]):
    """ converts django model to dictionary.
        ignores data that is in ignore list.
        includes data from foreign key objects, if it's not in exclude[] list.
        ignore takes precedence over exclude. """
    if not obj:
        return ''
    
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
    
    history = BillHistory(created_by = b.created_by,
                          bill = b, data = serialized_data)
    history.save()
    return True


@receiver(pre_save, sender=Category)
@receiver(pre_save, sender=Company)
@receiver(pre_save, sender=Product)
@receiver(pre_save, sender=ProductImage)
def cleanup_images(**kwargs):
    # if image was deleted or changed, add previous filename and path
    # to config.Cleanup model. Cleanup will delete listed objects on post_save() signal.
    try:
        prev_entry = kwargs['sender'].objects.get(id=kwargs['instance'].id)
    except: # the entry does not exist, no need to do anything
        return
        
    this_entry = kwargs['instance']
    
    if not prev_entry.image:
        # no image in previous entry, nothing to delete
        return
    
    if prev_entry.image.name != this_entry.image.name:
        # add image to Cleanup for later deletion
        c = Cleanup(filename=prev_entry.image.path)
        c.save()
        print prev_entry.image.name
