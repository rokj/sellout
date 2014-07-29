from django.conf.urls import patterns, url
from django.utils.translation import ugettext as _

from common import globals as g

from rest_framework.authtoken import views as authtoken_views

from pos.views import terminal
from pos.views.manage import manage
from pos.views.manage import company
from pos.views.manage import category
from pos.views.manage import product
from pos.views.manage import contact
from pos.views.manage import discount
from pos.views.manage import tax
from pos.views.manage import configuration
from pos.views.manage import till

from pos.views import bill

### common URL prefixes: ###
# company's site: /pos/blocklogic
# readable pattern: (?P<company>[\w-]{1,30})
r_company = r'^(?P<company>[\w-]{1,' + str(g.MISC['company_url_length']) + '})'
# system pages (registration, login, logout, ...: /pos/app/register-company
r_manage = g.MISC['management_url']

urlpatterns = patterns('',
    #
    # SYSTEM PAGES:
    #
    url(r_manage + '/' + _('register-company') + '$', company.register_company, name='register_company'),
    url(r_manage + '/' + r'url-name-suggestions$', company.url_name_suggestions, name='url_name_suggestions'),
    
    #token registration for api devices
    url(r_manage + '/' + r'api-token-auth/$', authtoken_views.obtain_auth_token),  # TODO

    #
    # MANAGEMENT:
    #
    # company
    url(r_company + '/' + r_manage + '/$', manage.manage_home, name='manage_home'),  # management home
    url(r_company + '/' + r_manage + _('/company') + '/$', company.edit_company, name='edit_company'),  # company
    url(r_company + '/' + r_manage + _('/upload-color-logo') + '/$', company.upload_color_logo, name='upload_color_logo'),
    url(r_company + '/' + r_manage + _('/upload-monochrome-logo') + '/$', company.upload_monochrome_logo, name='upload_monochrome_logo'),
    url(r_company + '/' + r_manage + '/monochrome_logo/' + '?$', company.create_monochrome_logo, name='create_monochrome_logo'),
    url(r_company + '/' + r_manage + _('/company-settings') + '/$', configuration.company_settings, name='company_settings'), # company settings
    # categories
    url(r_company + '/' + r_manage + _('/categories'), category.list_categories, name='list_categories'),  # list of categories
    url(r_company + '/' + r_manage + _('/category/add') + '/(?P<parent_id>-?\d+)?/$', category.add_category, name='add_category'),  # add
    url(r_company + '/' + r_manage + _('/category/edit') + '/(?P<category_id>\d+)/$', category.edit_category, name='edit_category'),  # edit
    url(r_company + '/' + r_manage + _('/category/delete') + '/$', category.delete_category, name='delete_category'),  # delete
    # contacts
    url(r_company + '/' + r_manage + _('/contacts') + '/$', contact.list_contacts, name='list_contacts'),
    url(r_company + '/' + r_manage + _('/contact/add') + '/$', contact.add_contact, name='add_contact'),
    url(r_company + '/' + r_manage + _('/contact/edit') + '/(?P<contact_id>\d+)/$', contact.edit_contact, name='edit_contact'),
    url(r_company + '/' + r_manage + _('/contact/delete') + '/$', contact.delete_contact, name='delete_contact'),
    # discounts
    url(r_company + '/' + r_manage + _('/discounts') + '/$', discount.list_discounts, name='list_discounts'),
    url(r_company + '/' + r_manage + _('/discount/add') + '/$', discount.add_discount, name='add_discount'),
    url(r_company + '/' + r_manage + _('/discount/edit') + '/(?P<discount_id>\d+)/$', discount.edit_discount, name='edit_discount'),
    url(r_company + '/' + r_manage + _('/discount/delete') + '/$', discount.delete_discount, name='delete_discount'),
    # taxes
    url(r_company + '/' + r_manage + _('/taxes') + '/$', tax.list_taxes, name='list_taxes'),  # template view
    url(r_company + '/' + r_manage + '/json/tax/edit/?$', tax.edit_tax, name='edit_tax'),  # get all taxes in a json list
    url(r_company + '/' + r_manage + '/json/taxes/delete/?$', tax.delete_tax, name='delete_tax'),  # get all taxes in a json list
    url(r_company + '/' + r_manage + '/json/taxes/set-default/?$', tax.set_default_tax, name='set_default_tax'),  # get all taxes in a json list
    # cash registers (the module is named 'till' to avoid confusion with registration)
    url(r_company + '/' + r_manage + _('/registers') + '/$', till.list_registers, name='list_registers'),
    url(r_company + '/' + r_manage + _('/register/add') + '/$', till.add_register, name='add_register'),
    url(r_company + '/' + r_manage + _('/register/edit') + '/(?P<register_id>\d+)/$', till.edit_register, name='edit_register'),
    url(r_company + '/' + r_manage + _('/register/delete') + '/$', till.delete_register, name='delete_register'),

    #url(r_company + _('/manage/taxes/edit') + '/$', manage.misc.edit_taxes, name='edit_taxes'),
    # products
    url(r_company + '/' + r_manage + _('/products') + '/$', product.products, name='products'),  # static (template) page
    url(r_company + '/' + r_manage + '/json/products/search/$', product.search_products, name='search_products'),  # product list (search) - json
    url(r_company + '/' + r_manage + '/json/products/add/$', product.create_product, name='create_product'),  # edit (save) product - json
    url(r_company + '/' + r_manage + '/json/products/get/$', product.get_product, name='get_product'),  # product list (search) - json
    url(r_company + '/' + r_manage + '/json/products/edit/$', product.edit_product, name='edit_product'),  # edit (save) product - json
    url(r_company + '/' + r_manage + '/json/products/delete/$', product.delete_product, name='delete_product'),  # edit (save) product - json

    # user
    url(r_company + '/' + r_manage + _('/user-settings') + '/$', configuration.user_settings, name='user_settings'),  # user settings

    # misc (ajax): urls not translated
    url(r_company + '/' + r_manage + '/json/categories/?$', category.JSON_categories, name='JSON_categories'), # categories list TODO: in use?
    url(r_company + '/' + r_manage + '/json/units/' + '?$', product.JSON_units, name='JSON_units'), # unit types list
    url(r_company + '/' + r_manage + '/json/discounts/' + '?$', discount.JSON_discounts, name='JSON_discounts'), # available discounts list
    url(r_company + '/' + r_manage + '/json/toggle-favorite/' + '?$', product.toggle_favorite, name='toggle_favorite'), # set/remove favorite prodcut

    #
    # TERMINAL:
    #
    # save terminal settings (will width and such)
    url(r_company + '/save/$', terminal.save, name='save_terminal'),
    url(r_company + '/set-register/$', terminal.set_register, name='set_register'),
    url(r_company + '/quick-contact/$', contact.quick_contacts, name='quick_contacts'),
    url(r_company + '/get-unpaid-bill/$', bill.get_unpaid_bill, name='get_unpaid_bill'),
    url(r_company + '/finish-bill/$', bill.finish_bill, name='finish_bill'),
    url(r_company + '/check-bill-status/$', bill.check_bill_status, name='check_bill_status'),

    # views for bill
    url(r_company + '/bill/save/$', bill.create_bill, name='create_bill'),  # adds an item to bill
    #url(r_company + '/bill/get-active/$', bill.get_active_bill, name='get_active_bill'),
    #url(r_company + '/bill/item/remove/$', bill.remove_item, name='remove_bill_item'), # removes Item from bill

    # and finally: home: POS terminal, directly
    url(r_company + '/$', terminal.terminal, name='terminal'),  # by url_name
)
