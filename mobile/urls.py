from django.conf.urls import patterns, url
from django.utils.translation import ugettext as _

from common import globals as g
from mobile.views.manage.company import get_company, edit_company
from mobile.views.manage.till import mobile_get_all_registers
from mobile.views.views import mobile_get_cut, mobile_get_units

from mobile.views import login
from mobile.views import bill
from mobile.views.manage import category
from mobile.views.manage import product
from mobile.views.manage import discount
from mobile.views.manage import tax
from mobile.views.manage import contact
from mobile.views.manage import configuration


### common URL prefixes: ###
# company's site: /pos/blocklogic
# readable pattern: (?P<company>[\w-]{1,30})

r_company = r'^(?P<company>[\w-]{1,' + str(g.MISC['company_url_length']) + '})'
# system pages (registration, login, logout, ...: /pos/app/register-company
r_manage = g.MISC['management_url'] + '/'

urlpatterns = patterns('',

    # LOGIN
    url(r'^mobile-login/(?P<backend>[\w-]+)$', login.obtain_auth_token),

    # categories
    url(r_company + r'/manage/json/category/add/?$', category.mobile_add_category, name='add_category'),
    url(r_company + r'/manage/json/category/edit/?$', category.mobile_edit_category, name='edit_category'), # edit
    url(r_company + r'/manage/json/category/delete/?$', category.mobile_delete_category, name='delete_category'), # delete
    url(r_company + r'/manage/json/categories/?$', category.mobile_JSON_categories_strucutred, name='JSON_categories'),
    url(r_company + r'/manage/json/categories/all/?$', category.mobile_JSON_categories, name='JSON_categories'),
    url(r_company + r'/manage/json/category/dumps', category.mobile_JSON_dump_categories, name='dump_category'),
    # contacts
    url(r_company + r'/manage/json/contacts/?$', contact.mobile_list_contacts, name='list_contacts'),
    url(r_company + r'/manage/json/contact/add/?$', contact.mobile_add_contact, name='add_contact'),
    url(r_company + r'/manage/json/contact/get/(?P<contact_id>\d+)/?$', contact.mobile_get_contact, name='get_contact'),
    url(r_company + r'/manage/json/contact/edit/', contact.mobile_edit_contact, name='edit_contact'),
    url(r_company + r'/manage/json/contact/delete/?$', contact.mobile_delete_contact, name='delete_contact'),


    # discounts
    url(r_company + r'/manage/json/discounts/?$', discount.mobile_list_discounts, name='get_discounts'),
    url(r_company + r'/manage/json/discounts/add/?$', discount.mobile_add_discount, name='add_dicount'),
    url(r_company + r'/manage/json/discounts/delete/?$', discount.mobile_delete_discount, name='delete_discount'),
    url(r_company + r'/manage/json/discounts/edit/?$', discount.mobile_edit_discount, name='edit_discount'),

    # units
    url(r_company + r'/manage/json/units/?$', mobile_get_units, name='get_units'),

    # taxes
    url(r_company + r'/manage/json/taxes/?$', tax.mobile_list_taxes, name='get_taxes'), # get all taxes in a json list
    url(r_company + r'/manage/json/taxes/edit/?$', tax.mobile_edit_tax, name='edit_tax'),
    url(r_company + r'/manage/json/taxes/save-default/?$', tax.mobile_save_default_tax, name='edit_tax'),
    url(r_company + r'/manage/json/taxes/delete/?$', tax.mobile_delete_tax, name='delete_tax'),
    # products
    url(r_company + r'/manage/json/products/?$', product.mobile_get_products, name='get_products'),
    url(r_company + r'/manage/json/products/search/?$', product.mobile_search_products, name='search_products'), # product list (search) - json

    url(r_company + r'/manage/json/products/add/?$', product.mobile_create_product, name='mobile_create_product'),
    url(r_company + r'/manage/json/products/get/(?P<product_id>\d+)/?$', product.mobile_get_product, name='get_product'), # product list (search) - json
    url(r_company + r'/manage/json/products/edit/?$', product.mobile_edit_product, name='edit_product'), # edit (save) product - json
    url(r_company + r'/manage/json/products/delete/?$', product.mobile_delete_prodcut, name='delete_product'), # edit (save) product - json
    url(r_company + r'/manage/json/products/favourite/?$', product.mobile_toggle_favorite, name='delete_product'), # edit (save) product - json

    # CUT (Categories, units, taxes)
    url(r_company + r'/manage/json/cut/get', mobile_get_cut, name='get_cut'), # get categories, units, taxes

    url(r_company + r'/manage/json/units/?$', product.mobile_JSON_units, name='mobile_JSON_units'),

    # Mr. Bill
    url(r_company + r'/manage/json/bill/add/?$', bill.mobile_create_bill, name='mobile_add_bill'),
    url(r_company + r'/manage/json/bill/finish/?$', bill.mobile_finish_bill, name='mobile_add_bill'),

    # configuration
    url(r_company + r'/manage/json/config/?$', configuration.get_mobile_config, name='mobile_get_config'),
    url(r_company + r'/manage/json/config/edit?$', configuration.save_company_config, name='mobile_get_config'),

    # company
    url(r_company + r'/manage/json/company/get', get_company, name='mobile_get_company'),
    url(r_company + r'/manage/json/company/edit', edit_company, name='mobile_edit_company'),

    url(r_company + r'/manage/json/registers/get', mobile_get_all_registers, name='mobile_get_registers'),

    # available discounts list
    # url(r_company + r'/manage/json/discounts/?$', discount.JSON_discounts, name='JSON_discounts'),
    
)
