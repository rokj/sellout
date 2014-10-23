
from django.http import JsonResponse

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from pos.models import Company, Category, Product, Tax, Discount, Contact
from pos.views.manage.category import category_to_dict
from pos.views.manage.contact import contact_to_dict
from pos.views.manage.discount import discount_to_dict
from pos.views.manage.product import product_to_dict
from pos.views.manage.tax import tax_to_dict, get_all_taxes
from pos.views.util import JsonError, JsonParse
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

    sync_objects = Sync.objects.only('seq')\
        .filter(company=company).order_by('seq')

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

    elif seq < last_key:

        ret['updated'] = False
        ret['drop'] = False
        seq_list = Sync.objects.filter(company=company, seq__gt=last_key).order_by('seq')

        items = []

        for seq_item in seq_list:
            item_ret = {'action': seq_item.action,
                        'model':  seq_item.model,
                        'object_id': seq_item.object_id}

            if seq_item.model == Category.__class__.__name__:
                c = Category.objects.get(id=seq_item.object_id)
                item_ret['item'] = category_to_dict(c, android=True)

            elif seq_item.model == Product.__class__.__name__:
                p = Product.objects.get(id=seq_item.object_id)
                item_ret['item'] = product_to_dict(request.user, company, p, android=True)

            elif seq_item.model == Tax.__class__.__name__:
                t = Tax.objects.get(id=seq_item.object_id)
                item_ret['item'] = tax_to_dict(request.user, company, t)

            elif seq_item.model == Discount.__class__.__name__:
                d = Discount.objects.get(id=seq_item.object_id)
                item_ret['item'] = discount_to_dict(request.user, company, d, android=True)

            elif seq_item.model == Category.__class__.__name__:
                con = Contact.objects.get(id=seq_item.object_id)
                item_ret['item'] = category_to_dict(con, android=True)

            items.append(item_ret)

        ret['items'] = items

    else:
        ret['updated'] = True

    return JsonResponse(ret, safe=False)