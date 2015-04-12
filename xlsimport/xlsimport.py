from django.db import transaction, IntegrityError
from django.utils.translation import ugettext as _
import common.globals as g
import decimal

from pos.models import Company, Category, Tax, Product, Price, PurchasePrice
import xlrd


def xls_import(filename, company, user):
    status = {
        'success': True,
        'error_messages': [],
        'info_messages': [],
    }

    def err(message, product_name=None, row=None, column=None):
        status['success'] = False
        status['error_messages'].append({'name': product_name, 'message': message, 'row': row, 'column': column})

    def info(message, product_name=None, row=None, column=None):
        status['info_messages'].append({'name': product_name, 'message': message, 'row': row, 'column': column})

    try:
        data = xlrd.open_workbook(filename)
        book = data.sheet_by_index(0)
    except:
        err(_("Opening the file failed"))
        return status

    def value(ir, ic):
        # returns cell value at specified row/column, formatted as text
        if book.cell_type(ir, ic) != xlrd.XL_CELL_TEXT:
            info(_("Cell value is not formatted as text"), None, ir, ic)

        return unicode(book.cell_value(ir, ic)).strip()

    nrows = book.nrows
    ncols = book.ncols

    # exact number of columns required: 12
    if ncols != 12:
        return err(_("Invalid number of columns, 12 required"), None, None)

    # a collection of all valid data;
    # if everything validates successfully, this will be inserted into database
    valid_products = []

    for irow in range(1, nrows):  # the first row contains titles, start with the second
        # Name
        # check if a product with that name exists already
        icol = 0
        cell = value(irow, icol)

        name = cell

        # Description
        # doesn't need checking
        icol = 1
        cell = value(irow, icol)

        description = cell

        # Code
        icol = 2
        cell = value(irow, icol)

        code = cell
        if Product.objects.filter(company=company, code=code).exists():
            err(_("A product with this name exists already"), name, irow, icol)

        # Tax (number only, check if tax exists in database)
        icol = 3
        cell = value(irow, icol)

        tax = None
        tax_amount = decimal.Decimal(1)
        try:
            tax_amount = decimal.Decimal(cell)
            tax = Tax.objects.get(company=company, amount=tax_amount)
        except Tax.DoesNotExist:
            err(_("Tax with this amount does not exist"), name, irow, icol)
        except (decimal.InvalidOperation, TypeError):
            err(_("Wrong number format for tax"), name)

        # Category (match by name or set no category to a product)
        icol = 4
        cell = value(irow, icol)

        if Category.objects.filter(company=company, name=cell).count() > 0:
            # if there are multiple categories with the same name, take the first by id
            # this should be the parent
            category = Category.objects.filter(company=company, name=cell).order_by('id')[0]
        else:
            category = None
            info(_("Category not found, none assigned"), name, irow, icol)

        # Stock
        icol = 5
        cell = value(irow, icol)

        stock = None
        try:
            stock = decimal.Decimal(cell)
        except (decimal.InvalidOperation, TypeError):
            err(_("Invalid number format for stock"), name, irow, icol)

        # Unit (anything that doesn't match the unit types list defaults to 'Piece')
        icol = 6
        cell = value(irow, icol)

        if cell not in g.UNIT_CODES:
            unit_type = g.UNIT_CODES[0]  # take a default
            info(_("No unit type matched, default taken"), name, irow, icol)
        else:
            unit_type = cell

        # Purchase price
        icol = 7
        cell = value(irow, icol)

        purchase_price = None
        try:
            purchase_price = decimal.Decimal(cell)
        except (decimal.InvalidOperation, TypeError):
            err(_("Invalid number format for purchase price"), name, irow, icol)

        # Sell price without tax
        icol = 8
        cell = value(irow, icol)

        try:
            price_without_tax = decimal.Decimal(cell)
        except (decimal.InvalidOperation, TypeError):
            price_without_tax = None
            # checking of this after parsing price with tax

        # Sell price with tax
        icol = 9
        cell = value(irow, icol)

        try:
            price_with_tax = decimal.Decimal(cell)
        except (decimal.InvalidOperation, TypeError):
            price_with_tax = None

        if price_without_tax is None and price_with_tax is None:
            err(_("No prices set or their number format is not valid"), name, irow, icol)

        # calculate prices
        if price_with_tax and price_without_tax is None:
            price_without_tax = price_with_tax / (decimal.Decimal(1) + (tax_amount / decimal.Decimal(100)))

        # Shortcut
        icol = 10
        cell = value(irow, icol)

        shortcut = cell

        # Private notes
        icol = 11
        cell = value(irow, icol)

        notes = cell

        # if there was no error, save all data for later use
        # if there was an error, don't even bother, the data won't be used anyway
        if status['success']:
            valid_products.append({
                'company': company,  # these are required for Product.save()
                'created_by': user,

                'name': name,
                'description': description,
                'code': code,
                'tax': tax,
                'category': category,
                'stock': stock,
                'unit_type': unit_type,
                'shortcut': shortcut,
                'private_notes': notes,

                'purchase_price': purchase_price,  # these must not be in **kwargs for Product.save()
                'price_without_tax': price_without_tax,
            })

    # all products have been validated;
    # if there was no error, start inserting stuff into database;
    # keep all in the same transaction
    if not status['success']:
        return status

    try:
        with transaction.atomic():
            for p in valid_products:
                # save product: take prices out, then use **kwargs
                price_without_tax = p['price_without_tax']
                del p['price_without_tax']

                purchase_price = p['purchase_price']
                del p['purchase_price']

                product = Product(**p)
                product.save()

                # save prices
                if not product.update_price(Price, user, price_without_tax):
                    err(_("Updating price failed"), product_name=p['name'])
                    raise Exception("Updating price failed")

                if not product.update_price(PurchasePrice, user, purchase_price):
                    err(_("Updating purchase price failed"), product_name=p['name'])
                    raise Exception("Updating purchase price failed")

            # that's it
            return status
    except IntegrityError:
        return status
