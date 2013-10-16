from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from pos.models import Company
from pos.views.manage import get_all_categories_structured

from pos.views.util import has_permission, no_permission_view, JSON_response, JSON_ok, JSON_parse, JSON_error
from config.functions import get_value, set_value
import common.globals as g

import json

def get_item_price():
    pass

def bill_item_to_dict(user, item):
    item = {}
    item['bill'] = bill.id
    item['quantity'] = format_number(user, item.quantity)
    #item['price'] = models.DecimalField(_("Sub total"), # hard-coded price from current Price table
    
    #discount_sum = models.DecimalField(_("Discount, absolute value, sum of all current discounts"), 
    #bill_notes = models.CharField(_("Bill notes") ,max_length=1000, null=True, blank=True,


def bill_to_dict(user, bill):
    bill = {}
    
    bill['type'] = bill.type
    bill['recipient_company'] = bill.recipient_company
    bill['recipient_contact'] = bill.recipient_contact
    bill['note'] = bill.note
    bill['sub_total'] = format_number(user, bill.sub_total)
    bill['discount'] = bill.discount
    bill['tax'] = bill.tax
    bill['timestamp'] = bill.timestamp
    bill['status'] = bill.status
    
    # items
    items = []
    #for i in bill.items:
        #items.add(

def get_active_bill(request, company):
    """ returns the  """
