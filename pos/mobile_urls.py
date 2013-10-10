from django.conf.urls import patterns, url
from django.utils.translation import ugettext as _

from common import globals as g
import pos.views as pos
import pos.views.manage as manage


from rest_framework.authtoken import views as authtoken_views



### common URL prefixes: ###
# company's site: /pos/blocklogic
# readable pattern: (?P<company>[\w-]{1,30})
r_company = r'^(?P<company>[\w-]{1,' + str(g.MISC['company_url_length']) + '})'
# system pages (registration, login, logout, ...: /pos/app/register-company
r_manage = g.MISC['management_url'] + '/'

urlpatterns = patterns('',
    # system pages
    url(r_manage + _('register-company') + '$', manage.company.register_company, name='register_company'),
    url(r_manage + r'url-name-suggestions$', manage.company.url_name_suggestions, name='url_name_suggestions'),
    
    #token registration for api devices
    #
    #TODO
    #
    url(r_manage + r'api-token-auth/?$', authtoken_views.obtain_auth_token),
    
    # home: POS terminal, directly
    url(r_company + '/?$', pos.terminal, name='terminal'), # by url_name
    # ajax calls for POS terminal
    
    
    # management urls: company
    url(r_company + _('/manage') + '/?$', manage.manage_home, name='manage_home'), # management home
    url(r_company + _('/manage/company') + '/?$', manage.company.edit_company, name='edit_company'), # company
    # categories
    url(r_company + _('/manage/categories') + '/?$', manage.category.list_categories, name='list_categories'), # list of categories
    url(r_company + r'/manage/json/category/add' + '/(?P<parent_id>-?\d+)/?$', manage.category.mobile_add_category, name='add_category'), # add
    url(r_company + r'/manage/json/category/get/(?P<category_id>\d+)/?$', manage.category.mobile_get_category, name='get_category'),
    url(r_company + r'/manage/json/category/edit/(?P<category_id>\d+)/?$', manage.category.mobile_edit_category, name='edit_category'), # edit
    url(r_company + _('/manage/category/delete') + '/(?P<category_id>\d+)/?$', manage.category.delete_category, name='delete_category'), # delete
    # contacts
    url(r_company + r'/manage/json/contacts/?$', manage.contact.mobile_list_contacts, name='list_contacts'),
    url(r_company + r'/manage/json/contacts/add/?$', manage.contact.mobile_add_contact, name='add_contact'),
    url(r_company + r'/manage/json/contacts/get/(?P<contact_id>\d+)/?$', manage.contact.mobile_get_contact, name='get_contact'),

    url(r_company + _('/manage/contact/edit') + '/(?P<contact_id>\d+)/?$', manage.contact.edit_contact, name='edit_contact'),
    url(r_company + _('/manage/contact/delete') + '/(?P<contact_id>\d+)/?$', manage.contact.delete_contact, name='delete_contact'),
    # discounts
    url(r_company + _('/manage/discounts') + '/?$', manage.discount.list_discounts, name='list_discounts'),
    url(r_company + _('/manage/discount/add') + '/?$', manage.discount.add_discount, name='add_discount'),
    url(r_company + _('/manage/discount/edit') + '/(?P<discount_id>\d+)/?$', manage.discount.edit_discount, name='edit_discount'),
    url(r_company + _('/manage/discount/delete') + '/(?P<discount_id>\d+)/?$', manage.discount.delete_discount, name='delete_discount'),
    # products
    url(r_company + _('/manage/products') + '/?$', manage.product.products, name='products'), # static (template) page
    url(r_company + r'/manage/json/products/search/?$', manage.product.mobile_search_products, name='search_products'), # product list (search) - json
    url(r_company + r'/manage/json/products/add/?$', manage.product.mobile_create_product, name='mobile_create_product'), # edit (save) product - json
    url(r_company + r'/manage/json/products/get/(?P<product_id>\d+)/?$', manage.product.mobile_get_product, name='get_product'), # product list (search) - json
    url(r_company + r'/manage/json/products/edit/(?P<product_id>\d+)/?$', manage.product.mobile_edit_product, name='edit_product'), # edit (save) product - json
    url(r_company + r'/manage/json/products/delete/(?P<product_id>\d+)/?$', manage.product.delete_product, name='delete_product'), # edit (save) product - json
    # users
    #url(r_company + _('/manage/users') + '/?$', manage.users.edit_company, name='edit_users'), # company
    # config (company parameter is needed only for url; configuration is per user, regardless of company
    url(r_company + _('/manage/configuration') + '/?$', manage.configuration.edit_config, name='edit_config'), # company
    
    
    # misc (ajax): urls not translated
    url(r_company + r'/manage/json/categories/?$', manage.category.mobile_JSON_categories, name='JSON_categories'),
    
    # unit types list
    #
    # TODO
    #
    url(r_company + r'/manage/json/units/?$', manage.product.mobile_JSON_units, name='mobile_JSON_units'),
    
    # available discounts list
    url(r_company + r'/manage/json/discounts/?$', manage.discount.JSON_discounts, name='JSON_discounts'),
    
)
