from django.conf.urls import patterns, url
from django.utils.translation import ugettext as _

from views import manage, home
from common import globals as g

### common URL prefixes: ###
# readable pattern: (omitted translation and globals)
# (?P<company>[\w-]{1,30})
r_company = r'(?P<company>[\w-]{1,' + str(g.MISC['company_url_length']) + '})'

# the list, finally
urlpatterns = patterns('',
    # registration urls
    url(_('register-company') + '$', manage.register_company, name='register_company'),
    url(r'url-name-suggestions$', manage.url_name_suggestions, name='url_name_suggestions'),
    
    # home: POS terminal directly
    url(r_company + '$', home.terminal, name='terminal'), # by url_name

    # management urls
    url(r_company + _('/manage/company') + '$', manage.edit_company_details, name='edit_company_details'),
)
