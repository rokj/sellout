
from django.http import JsonResponse
# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from pos.models import Company, Category, Product, Tax, Discount, Contact, Register
from pos.views.manage.category import category_to_dict
from pos.views.manage.contact import contact_to_dict
from pos.views.manage.discount import discount_to_dict
from pos.views.manage.product import product_to_dict
from pos.views.manage.register import register_to_dict
from pos.views.manage.tax import tax_to_dict, get_all_taxes
from common.functions import JsonError, JsonParse
from sync.models import Sync

from django.utils.translation import ugettext as _


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated,))
def mobile_sync_db(request, company):

    try:
        company = Company.objects.get(url_name=company)
    except Company.DoesNotExist:
        return JsonError(_("Company does not exist"))

    data = JsonParse(request.POST['data'])
    seq = data['database_version']
    device_id = data['device_id']

    sync_objects = Sync.objects.only('seq')\
        .filter(company=company).order_by('-seq')

    last_key = 0

    if len(sync_objects) > 0:
        last_key = sync_objects[0].seq

    ret = {'version': last_key}

    if seq == 0 or last_key - 5000 > seq:

        # if first sync or sync outdated, why not load whole DB

        ret['updated'] = False
        ret['drop'] = True

        # get taxes
        ret['taxes'] = get_all_taxes(request.user, company)

        # get contacts
        contacts = Contact.objects.filter(company=company)
        cs = []
        for contact in contacts:
            cs.append(contact_to_dict(request.user, company, contact))

        ret['contacts'] = cs

        # get categories
        categories = Category.objects.filter(company=company)
        ct = []

        for category in categories:
            ct.append(category_to_dict(category, android=True))

        ret['categories'] = ct

        # get discounts
        discounts = Discount.objects.filter(company=company)
        ds = []

        for discount in discounts:
            ds.append(discount_to_dict(request.user, company, discount, android=True))

        ret['discounts'] = ds

        # get products
        products = Product.objects.filter(company=company)
        pr = []
        for product in products:
            pr.append(product_to_dict(request.user, company, product, android=True))

        ret['products'] = pr

        try:
            register = Register.objects.get(company=company, device_id=device_id)
            ret['register'] = register_to_dict(request.user, company, register)
        except Register.DoesNotExist:
            ret['register'] = None

    elif seq < last_key:

        ret['updated'] = False
        ret['drop'] = False
        seq_list = Sync.objects.filter(company=company, seq__lte=last_key).order_by('seq')

        items = []

        for seq_item in seq_list:
            item_ret = {'action': seq_item.action,
                        'model':  seq_item.model,
                        'object_id': seq_item.object_id}

            if seq_item.action == 'save':
                if seq_item.model == 'Category':
                    c = Category.objects.get(id=seq_item.object_id)
                    item_ret['item'] = category_to_dict(c, android=True)

                elif seq_item.model == 'Product':
                    p = Product.objects.get(id=seq_item.object_id)
                    item_ret['item'] = product_to_dict(request.user, company, p, android=True)

                elif seq_item.model == 'Tax':
                    t = Tax.objects.get(id=seq_item.object_id)
                    item_ret['item'] = tax_to_dict(request.user, company, t)

                elif seq_item.model == 'Discount':
                    d = Discount.objects.get(id=seq_item.object_id)
                    item_ret['item'] = discount_to_dict(request.user, company, d, android=True)

                elif seq_item.model == 'Contact':
                    con = Contact.objects.get(id=seq_item.object_id)
                    item_ret['item'] = contact_to_dict(request.user, company, con)

                elif seq_item.model == 'Register':
                    r = Register.objects.get(id=seq_item.object_id)
                    item_ret['item'] = register_to_dict(request.user, company, r)


            items.append(item_ret)

        ret['items'] = items

    else:
        ret['updated'] = True

    return JsonResponse(ret, safe=False)