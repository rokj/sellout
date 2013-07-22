class Category(models.Model):
    """
    Basic hierarchical category model for storing products
    """
    site = models.ForeignKey(Site, verbose_name=_('Site'))
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), help_text=_("Used for URLs, auto-generated from name if blank"), blank=True)
    parent = models.ForeignKey('self', blank=True, null=True,
        related_name='child')
    meta = models.TextField(_("Meta Description"), blank=True, null=True,
        help_text=_("Meta description for this category"))
    description = models.TextField(_("Description"), blank=True,
        help_text="Optional")
    ordering = models.IntegerField(_("Ordering"), default=0, help_text=_("Override alphabetical order in category display"))
    is_active = models.BooleanField(_("Active"), default=True, blank=True)
    related_categories = models.ManyToManyField('self', blank=True, null=True,
        verbose_name=_('Related Categories'), related_name='related_categories')
    objects = CategoryManager()

class CategoryImage(models.Model):
    """
    A picture of an item.  Can have many pictures associated with an item.
    Thumbnails are automatically created.
    """
    category = models.ForeignKey(Category, null=True, blank=True,
        related_name="images")
    picture = ImageWithThumbnailField(verbose_name=_('Picture'),
        upload_to="__DYNAMIC__",
        name_field="_filename",
        max_length=200) #Media root is automatically prepended
    caption = models.CharField(_("Optional caption"), max_length=100,
        null=True, blank=True)
    sort = models.IntegerField(_("Sort Order"), default=0)

class Discount(models.Model):
    """
    Allows for multiple types of discounts including % and dollar off.
    Also allows finite number of uses.
    """
    site = models.ForeignKey(Site, verbose_name=_('site'))
    description = models.CharField(_("Description"), max_length=100)
    code = models.CharField(_("Discount Code"), max_length=20, unique=True,
        help_text=_("Coupon Code"))
    active = models.BooleanField(_("Active"))
    amount = CurrencyField(_("Discount Amount"), decimal_places=2,
        max_digits=8, blank=True, null=True,
        help_text=_("Enter absolute discount amount OR percentage."))
    percentage = models.DecimalField(_("Discount Percentage"), decimal_places=2,
        max_digits=5, blank=True, null=True,
        help_text=_("Enter absolute discount amount OR percentage.  Percents are given in whole numbers, and can be up to 100%."))
    automatic = models.NullBooleanField(_("Is this an automatic discount?"), default=False, blank=True,
        null=True, help_text=_("Use this field to advertise the discount on all products to which it applies.  Generally this is used for site-wide sales."))
    allowedUses = models.IntegerField(_("Number of allowed uses"),
        blank=True, null=True, help_text=_('Set this to a number greater than 0 to have the discount expire after that many uses.'))
    numUses = models.IntegerField(_("Number of times already used"),
        blank=True, null=True)
    minOrder = CurrencyField(_("Minimum order value"),
        decimal_places=2, max_digits=8, blank=True, null=True)
    startDate = models.DateField(_("Start Date"))
    endDate = models.DateField(_("End Date"))
    shipping = models.CharField(_("Shipping"), choices=DISCOUNT_SHIPPING_CHOICES,
        default='NONE', blank=True, null=True, max_length=10)
    allValid = models.BooleanField(_("All products?"), default=False,
        help_text=_('Apply this discount to all discountable products? If this is false you must select products below in the "Valid Products" section.'))
    valid_products = models.ManyToManyField('Product', verbose_name=_("Valid Products"),
        blank=True, null=True)
    valid_categories = models.ManyToManyField('Category', verbose_name=_("Valid Categories"),
        blank=True, null=True)

class Product(models.Model):
    """
    Root class for all Products
    """
    site = models.ForeignKey(Site, verbose_name=_('Site'))
    name = models.CharField(_("Full Name"), max_length=255, blank=False,
        help_text=_("This is what the product will be called in the default site language.  To add non-default translations, use the Product Translation section below."))
    slug = models.SlugField(_("Slug Name"), blank=True,
        help_text=_("Used for URLs, auto-generated from name if blank"), max_length=255)
    sku = models.CharField(_("SKU"), max_length=255, blank=True, null=True,
        help_text=_("Defaults to slug if left blank"))
    short_description = models.TextField(_("Short description of product"), help_text=_("This should be a 1 or 2 line description in the default site language for use in product listing screens"), max_length=200, default='', blank=True)
    description = models.TextField(_("Description of product"), help_text=_("This field can contain HTML and should be a few paragraphs in the default site language explaining the background of the product, and anything that would help the potential customer make their purchase."), default='', blank=True)
    category = models.ManyToManyField(Category, blank=True, verbose_name=_("Category"))
    items_in_stock = models.DecimalField(_("Number in stock"),  max_digits=18, decimal_places=6, default='0')
    meta = models.TextField(_("Meta Description"), max_length=200, blank=True, null=True, help_text=_("Meta description for this product"))
    date_added = models.DateField(_("Date added"), null=True, blank=True)
    active = models.BooleanField(_("Active"), default=True, help_text=_("This will determine whether or not this product will appear on the site"))
    featured = models.BooleanField(_("Featured"), default=False, help_text=_("Featured items will show on the front page"))
    ordering = models.IntegerField(_("Ordering"), default=0, help_text=_("Override alphabetical order in category display"))
    weight = models.DecimalField(_("Weight"), max_digits=8, decimal_places=2, null=True, blank=True)
    weight_units = models.CharField(_("Weight units"), max_length=3, null=True, blank=True)
    length = models.DecimalField(_("Length"), max_digits=6, decimal_places=2, null=True, blank=True)
    length_units = models.CharField(_("Length units"), max_length=3, null=True, blank=True)
    width = models.DecimalField(_("Width"), max_digits=6, decimal_places=2, null=True, blank=True)
    width_units = models.CharField(_("Width units"), max_length=3, null=True, blank=True)
    height = models.DecimalField(_("Height"), max_digits=6, decimal_places=2, null=True, blank=True)
    height_units = models.CharField(_("Height units"), max_length=3, null=True, blank=True)
    related_items = models.ManyToManyField('self', blank=True, null=True, verbose_name=_('Related Items'), related_name='related_products')
    also_purchased = models.ManyToManyField('self', blank=True, null=True, verbose_name=_('Previously Purchased'), related_name='also_products')
    total_sold = models.DecimalField(_("Total sold"),  max_digits=18, decimal_places=6, default='0')
    taxable = models.BooleanField(_("Taxable"), default=lambda: config_value('TAX', 'PRODUCTS_TAXABLE_BY_DEFAULT'))
    taxClass = models.ForeignKey('TaxClass', verbose_name=_('Tax Class'), blank=True, null=True, help_text=_("If it is taxable, what kind of tax?"))
    shipclass = models.CharField(_('Shipping'), choices=SHIP_CLASS_CHOICES, default="DEFAULT", max_length=10,
        help_text=_("If this is 'Default', then we'll use the product type to determine if it is shippable."))

class ProductAttribute(models.Model):
    """
    Allows arbitrary name/value pairs (as strings) to be attached to a product.
    This is a simple way to add extra text or numeric info to a product.
    If you want more structure than this, create your own subtype to add
    whatever you want to your Products.
    """
    product = models.ForeignKey(Product)
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES, null=True, blank=True)
    option = models.ForeignKey(AttributeOption)
    value = models.CharField(_("Value"), max_length=255)

class CategoryAttribute(models.Model):
    """
    Similar to ProductAttribute, except that this is for categories.
    """
    category = models.ForeignKey(Category)
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES, null=True, blank=True)
    option = models.ForeignKey(AttributeOption)
    value = models.CharField(_("Value"), max_length=255)

class Price(models.Model):
    """
    A Price!
    Separating it out lets us have different prices for the same product for different purposes.
    For example for quantity discounts.
    The current price should be the one with the earliest expires date, and the highest quantity
    that's still below the user specified (IE: ordered) quantity, that matches a given product.
    """
    product = models.ForeignKey(Product)
    price = CurrencyField(_("Price"), max_digits=14, decimal_places=6, )
    quantity = models.DecimalField(_("Discount Quantity"), max_digits=18,
        decimal_places=6, default='1.0',
        help_text=_("Use this price only for this quantity or higher"))
    expires = models.DateField(_("Expires"), null=True, blank=True)
    #TODO: add fields here for locale/currency specific pricing

class ProductImage(models.Model):
    """
    A picture of an item.  Can have many pictures associated with an item.
    Thumbnails are automatically created.
    """
    product = models.ForeignKey(Product, null=True, blank=True)
    picture = ImageWithThumbnailField(verbose_name=_('Picture'),
        upload_to="__DYNAMIC__",
        name_field="_filename",
        max_length=200) #Media root is automatically prepended
    caption = models.CharField(_("Optional caption"), max_length=100,
        null=True, blank=True)
    sort = models.IntegerField(_("Sort Order"), default=0)

class ProductImageTranslation(models.Model):
    """A specific language translation for a `ProductImage`.  This is intended for all descriptions which are not the
    default settings.LANGUAGE.
    """
    productimage = models.ForeignKey(ProductImage, related_name="translations")
    languagecode = models.CharField(_('language'), max_length=10, choices=settings.LANGUAGES)
    caption = models.CharField(_("Translated Caption"), max_length=255, )
    version = models.IntegerField(_('version'), default=1)
    active = models.BooleanField(_('active'), default=True)

class TaxClass(models.Model):
    """
    Type of tax that can be applied to a product.  Tax
    might vary based on the type of product.  In the US, clothing could be
    taxed at a different rate than food items.
    """
    title = models.CharField(_("Title"), max_length=20,
        help_text=_("Displayed title of this tax."))
    description = models.CharField(_("Description"), max_length=30,
        help_text=_("Description of products that would be taxed."))

