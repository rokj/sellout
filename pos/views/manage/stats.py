from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Sum, Q, Count
from django.shortcuts import render
from pytz import timezone
from common.decorators import login_required
from django.utils.translation import ugettext as _
from common.globals import PAID
from config.functions import get_company_value, get_date_format

from pos.models import Company, Bill, BillItem
from common.functions import has_permission, no_permission_view, format_number, parse_date, format_date

from common import globals as g
import datetime as dtm


@login_required
def stats(request, company):
    c = Company.objects.get(url_name=company)

    # permission?
    if not has_permission(request.user, c, 'stats', 'view'):
        return no_permission_view(request, c, _("You have no permission to view stats"))

    # recent earnings: all bills from today/yesterday/this week/this month,
    # their income and profit
    def bill_earnings(start_date=None, end_date=None):
        billset = Bill.objects.filter(company=c, payment__status=PAID)

        if start_date:
            billset = billset.filter(timestamp__gte=start_date)

        if end_date:
            billset = billset.filter(timestamp__lte=end_date)

        if billset.count() == 0:
            return {
                'income': format_number(request.user, c, Decimal(0)),
                'profit': format_number(request.user, c, Decimal(0)),
            }

        income = billset.aggregate(Sum('payment__total'))['payment__total__sum']

        return {
            'income': format_number(request.user, c, income),
            'profit': format_number(request.user, c,
                        income - billset.aggregate(Sum('base'))['base__sum'] -
                        billset.aggregate(Sum('discount'))['discount__sum'])
        }

    today = dtm.datetime.utcnow().replace(tzinfo=timezone(get_company_value(request.user, c, 'pos_timezone')))
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)

    # get custom dates from form, if they are present
    earnings_from = None
    earnings_to = None

    if request.method == "GET":
        r = parse_date(request.user, c, request.GET.get('earnings_from'))
        if not r['success']:
            earnings_from = None
        else:
            earnings_from = r['date']

        r = parse_date(request.user, c, request.GET.get('earnings_to'))
        if not r['success']:
            earnings_to = None
        else:
            earnings_to = r['date']

        if earnings_from > earnings_to:
            earnings_from = None
            earnings_to = None

    if earnings_from and earnings_to:
        custom_earnings = bill_earnings(start_date=earnings_from, end_date=earnings_to)
    else:
        custom_earnings = None

    earnings = {
        'today': bill_earnings(start_date=today),
        'yesterday': bill_earnings(start_date=today - dtm.timedelta(days=1), end_date=today),
        'week': bill_earnings(start_date=today - dtm.timedelta(days=today.weekday())),
        'month': bill_earnings(start_date=today.replace(day=1)),
        'custom': custom_earnings
    }

    # top-selling products:
    # today/yesterday/this week/this/month/overall
    # TODO

    context = {
        'company': c,
        'earnings': earnings,
        'earnings_from': format_date(request.user, c, earnings_from),
        'earnings_to': format_date(request.user, c, earnings_to),

        'title': _("Stats"),
        'site_title': g.SITE_TITLE,
        'date_format_js': get_date_format(request.user, c, 'js')
    }

    return render(request, 'pos/manage/stats.html', context)