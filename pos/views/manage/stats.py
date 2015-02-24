from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from common.decorators import login_required
from django.utils.translation import ugettext as _
from django import forms
from django.http import Http404, HttpResponseRedirect, JsonResponse

from pos.models import Company, Category, Product
from common.functions import JsonError, JsonParse, JsonOk,  \
    has_permission, no_permission_view, JsonStringify

from common import globals as g

import random


def stats(request, company):
    c = Company.objects.get(url_name=company)

    # recent earnings: all bills from today/yesterday/this week/this month,
    # their income and profit



    # top-selling products: today/yesterday/this week/this/month/overall


    context = {
        'company': c,
    }

    return render(request, 'pos/manage/stats.html', context)