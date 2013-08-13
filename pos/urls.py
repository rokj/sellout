from django.conf.urls import patterns, url
from django.utils.translation import ugettext as _

from views import manage, home
from common import globals as g

### common URL prefixes: ###
# company's site: /pos/blocklogic
# readable pattern: (?P<company>[\w-]{1,30})
r_company = r'^(?P<company>[\w-]{1,' + str(g.MISC['company_url_length']) + '})'
# system pages (registration, login, logout, ...: /pos/app/register-company
r_manage = g.MISC['management_url'] + '/'

urlpatterns = patterns('',
    # system pages
    url(r_manage + _('register-company') + '$', manage.register_company, name='register_company'),
    url(r_manage + r'url-name-suggestions$', manage.url_name_suggestions, name='url_name_suggestions'),
    
    # home: POS terminal, directly
    url(r_company + '/?$', home.terminal, name='home'), # by url_name
    
    # management urls: company
    url(r_company + _('/manage') + '/?$', manage.manage_home, name='manage_home'), # management home
    url(r_company + _('/manage/company') + '/?$', manage.edit_company, name='edit_company'), # company
    # categories
    url(r_company + _('/manage/categories') + '/?$', manage.list_categories, name='list_categories'), # list of categories
    url(r_company + _('/manage/category/add') + '/(?P<parent_id>-?\d+)/?$', manage.add_category, name='add_category'), # add
    url(r_company + _('/manage/category/edit') + '/(?P<category_id>\d+)/?$', manage.edit_category, name='edit_category'), # edit
    url(r_company + _('/manage/category/delete') + '/(?P<category_id>\d+)/?$', manage.delete_category, name='delete_category'), # delete
    # contacts
    url(r_company + _('/manage/contacts') + '/?$', manage.list_contacts, name='list_contacts'),
    url(r_company + _('/manage/contact/add') + '/?$', manage.add_contact, name='add_contact'),
    url(r_company + _('/manage/contact/edit') + '/(?P<contact_id>\d+)/?$', manage.edit_contact, name='edit_contact'),
    url(r_company + _('/manage/contact/delete') + '/(?P<contact_id>\d+)/?$', manage.delete_contact, name='delete_contact'),
    # discounts
    url(r_company + _('/manage/discounts') + '/?$', manage.list_discounts, name='list_discounts'),
    url(r_company + _('/manage/discount/add') + '/?$', manage.add_discount, name='add_discount'),
    url(r_company + _('/manage/discount/edit') + '/(?P<discount_id>\d+)/?$', manage.edit_discount, name='edit_discount'),
    url(r_company + _('/manage/discount/delete') + '/(?P<discount_id>\d+)/?$', manage.delete_discount, name='delete_discount'),
    # products
    url(r_company + _('/manage/products') + '/?$', manage.products, name='products'),
    
    # AJAX stuff:
    # categories
    url(r_company + _('/manage/json/categories') + '/?$', manage.JSON_categories, name='JSON_categories'),
    # product list (after search)
    url(r_company + _('/manage/json/products') + '/?$', manage.search_products, name='search_products'),
    
    
    
)
