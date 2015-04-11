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
from pos.views.manage import stats
from pos.views.manage import tax
from pos.views.manage import configuration
from pos.views.manage import register
from pos.views.manage import bill
from pos.views.manage import users

from pos.views import bill as terminal_bill

import xlsimport

### common URL prefixes: ###
# company's site: /pos/blocklogic
# readable pattern: (?P<company>[\w-]{1,30})
r_company = r'^(?P<company>[\w-]{1,' + str(g.MISC['company_url_length']) + '})'
# system pages (registration, login, logout, ...: /pos/app/register-company
r_manage = g.MISC['management_url']

urlpatterns = patterns('',
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
    url(r_company + '/' + r_manage + _('/category/delete') + '/$', category.web_delete_category, name='delete_category'),  # delete
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

    # stats
    url(r_company + '/' + r_manage + _('/stats') + '/$', stats.stats, name='stats'),

    # taxes
    url(r_company + '/' + r_manage + _('/taxes') + '/$', tax.list_taxes, name='list_taxes'),  # template view
    url(r_company + '/' + r_manage + '/json/tax/edit/?$', tax.edit_tax, name='edit_tax'),  # get all taxes in a json list
    url(r_company + '/' + r_manage + '/json/taxes/delete/?$', tax.delete_tax, name='delete_tax'),  # get all taxes in a json list
    url(r_company + '/' + r_manage + '/json/taxes/set-default/?$', tax.set_default_tax, name='set_default_tax'),  # get all taxes in a json list
    # cash registers
    url(r_company + '/' + r_manage + _('/registers') + '/$', register.list_registers, name='list_registers'),
    url(r_company + '/' + r_manage + _('/register/add') + '/$', register.add_register, name='add_register'),
    url(r_company + '/' + r_manage + _('/register/edit') + '/(?P<register_id>\d+)/$', register.edit_register, name='edit_register'),
    url(r_company + '/' + r_manage + _('/register/delete') + '/$', register.delete_register, name='delete_register'),

    # products
    url(r_company + '/' + r_manage + _('/products') + '/$', product.products, name='products'),  # static (template) page
    url(r_company + '/' + r_manage + '/json/products/search/$', product.search_products, name='search_products'),  # product list (search) - json
    url(r_company + '/' + r_manage + '/json/products/add/$', product.create_product, name='create_product'),  # edit (save) product - json
    url(r_company + '/' + r_manage + '/json/products/get/$', product.get_product, name='get_product'),  # product list (search) - json
    url(r_company + '/' + r_manage + '/json/products/edit/$', product.edit_product, name='edit_product'),  # edit (save) product - json
    url(r_company + '/' + r_manage + '/json/products/delete/$', product.delete_product, name='delete_product'),  # edit (save) product - json
    url(r_company + '/' + r_manage + '/json/products/mass-edit/$', product.mass_edit, name='mass_edit'),  # edit (save) product - json

    url(r_company + '/' + r_manage + '/json/products/import/$', product.import_xls, name='import_xls'),

    # users
    url(r_company + '/' + r_manage + _('/users') + '/$', users.list_users, name='list_users'),
    url(r_company + '/' + r_manage + _('/users/edit'), users.edit_permission, name='edit_permission'),
    url(r_company + '/' + r_manage + _('/users/delete') + '/$', users.delete_permission, name='delete_permission'),

    url(r_company + '/' + r_manage + _('/users/invite') + '/$', users.invite_users, name='invite_users'),
    url(r_company + '/' + r_manage + _('/users/delete-invitation') + '/$', users.delete_invitation, name='delete_invitation'),

    # bill management
    url(r_company + '/' + r_manage + _('/bills') + '/$', bill.list_bills, name='list_bills'),

    # user
    url(r_company + '/' + r_manage + _('/user-settings') + '/$', configuration.user_settings, name='user_settings'),  # user settings

    # misc (ajax): urls not translated
    url(r_company + '/' + r_manage + '/json/categories/?$', category.JSON_categories, name='JSON_categories'), # categories list TODO: in use?
    url(r_company + '/' + r_manage + '/json/units/' + '?$', product.JSON_units, name='JSON_units'), # unit types list
    url(r_company + '/' + r_manage + '/json/discounts/' + '?$', discount.json_discounts, name='json_discounts'), # available discounts list
    url(r_company + '/' + r_manage + '/json/toggle-favorite/' + '?$', product.toggle_favorite, name='toggle_favorite'), # set/remove favorite prodcut

    #
    # TERMINAL:
    #
    # save terminal settings (will width and such)
    url(r_company + r'/save/$', terminal.save, name='save_terminal'),
    url(r_company + r'/quick-contact/$', contact.quick_contacts, name='quick_contacts'),
    url(r_company + r'/finish-bill/$', terminal_bill.finish_bill, name='finish_bill'),
    url(r_company + r'/check-bill-status/$', terminal_bill.check_bill_status, name='check_bill_status'),
    url(r_company + r'/get-unpaid-bills/$', terminal_bill.get_unpaid_bills, name='get_unpaid_bills'),
    url(r_company + r'/delete-unpaid-bill/$', terminal_bill.delete_unpaid_bill, name='delete_unpaid_bill'),
    url(r_company + r'/view-bill/$', terminal_bill.view_bill, name='view_bill'),
    url(r_company + r'/get-payment-btc-info/$', terminal_bill.get_payment_btc_info, name='get_payment_btc_info'),
    url(r_company + r'/change-payment-type/$', terminal_bill.change_payment_type, name='change_payment_type'),
    url(r_company + r'/paypal-send-invoice/$', terminal_bill.send_invoice, name='send_invoice'),

    # views for bill
    url(r_company + '/bill/save/$', terminal_bill.create_bill, name='create_bill'),  # adds an item to bill
    #url(r_company + '/bill/get-active/$', bill.get_active_bill, name='get_active_bill'),
    #url(r_company + '/bill/item/remove/$', bill.remove_item, name='remove_bill_item'), # removes Item from bill

    #
    # locking the screen (session, actually)
    # this must work on any page except index (and the unlock view, of course)
    #
    # lock (sets request.session['locked'] = True)
    url(r_company + r'/lock-session/$', terminal.lock_session, name='lock_session'),
    # the page that shows up when a user is logged in but the session is locked
    # this is only shown when visiting static pages (management) with locked session
    # unlocking will redirect to the page that the user wanted to visit
    url(r_company + r'/locked-session/$', terminal.locked_session, name='locked_session'),
    # unlocking
    url(r_company + r'/unlock-session/$', terminal.unlock_session, name='unlock_session'),

    # and finally: home: POS terminal, directly
    url(r_company + '/$', terminal.terminal, name='terminal'),  # by url_name
)
