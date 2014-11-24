from django.conf.urls import patterns, include, url

from blusers import views as blusers_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from views import index, select_company

admin.autodiscover()

urlpatterns = patterns('',
    # admin
    url(r'^admin/', include(admin.site.urls)),

    # main
    url(r'^$', index, name='index'),
    url(r'^logout/$', blusers_views.logout, name="logout"), # registration
    url(r'^lost-password/$', blusers_views.lost_password, name='lost-password'),

    url(r'^select-company/$', select_company, name='select-company'),

    # POS
    url(r'^pos/', include('pos.urls', namespace='pos')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('webpos',)}),
    
    # MOBILE
    url(r'^pos/mobile/', include('mobile.urls', namespace='mobile_pos')),
    url(r'^pos/sync/', include('sync.urls', namespace='sync')),
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