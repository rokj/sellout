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
    
    # management urls
    url(r_company + _('/manage') + '/?$', manage.manage_home, name='manage_home'), # management home
    url(r_company + _('/manage/company') + '/?$', manage.edit_company, name='edit_company'), # company
    url(r_company + _('/manage/categories') + '/?$', manage.list_categories, name='list_categories'), # list of categories
    url(r_company + _('/manage/category') + '/(?P<category_id>-?\d+)/?$', manage.edit_category, name='edit_category'), # category
    url(r_company + _('/manage/contact') + '/(?P<contact_id>-?\d+)/?$', manage.edit_contact, name='edit_contact'), # contact
    
)
