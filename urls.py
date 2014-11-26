from django.conf.urls import patterns, include, url

from blusers import views as blusers_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from views import index, select_company

admin.autodiscover()

urlpatterns = patterns('',
    # admin
    url(r'^admin/', include(admin.site.urls)),

    # main: the 'site' pages
    url(r'^$', index, name='index'),
    url(r'^sign-up/$', blusers_views.sign_up, name='sign_up'),
    url(r'^register-company/$', blusers_views.sign_up, name='register_company'),  # TODO: wrong view, this is
    url(r'^logout/$', blusers_views.logout, name="logout"),  # registration

    # registration: passwords, activations, etc.
    url(r'^activate-account/key=(?P<key>[\w]+)$', blusers_views.activate_account, name='activate_account'),
    url(r'^lost-password/$', blusers_views.lost_password, name='lost_password'),

    # actions: invitations, ...
    # TODO

    # selecting
    url(r'^select-company/$', select_company, name='select_company'),

    # POS
    url(r'^pos/', include('pos.urls', namespace='pos')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('webpos',)}),
    
    # MOBILE
    url(r'^pos/mobile/', include('mobile.urls', namespace='mobile_pos')),
    url(r'^pos/sync/', include('sync.urls', namespace='sync')),

    # the captcha app
    url(r'^captcha/', include('captcha.urls')),
)

# TODO: remove from production
from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
)

