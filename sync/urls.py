from django.conf.urls import patterns, url

from common import globals as g

from sync.views import mobile_sync_db

r_company = r'^(?P<company>[\w-]{1,' + str(g.MISC['company_url_length']) + '})'


urlpatterns = patterns('',

    # LOGIN

    url(r_company + r'/sync-database?$', mobile_sync_db, name='syncdb'), # syncdb


    # categories

    # available discounts list
    # url(r_company + r'/manage/json/discounts/?$', discount.json_discounts, name='json_discounts'),
    
)
