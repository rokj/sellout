from django.conf.urls import patterns, include, url
from django.contrib import admin

from blusers import views as blusers_views
from web import views as web_views

admin.autodiscover()

urlpatterns = patterns('',
    # admin
    url(r'^admin/', include(admin.site.urls)),

    # POS app
    url(r'^pos/', include('pos.urls', namespace='pos')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('webpos',)}),
    
    # MOBILE urls
    url(r'^pos/mobile/', include('mobile.urls', namespace='mobile_pos')),
    url(r'^pos/sync/', include('sync.urls', namespace='sync')),

    # mobile
    # url(r'^' + 'mobile-register/$', blusers_views.mobile_register, name="mobile_register"),  # mobile registration
    url(r'^' + 'mobile-login/(?P<backend>[\w-]+)$', blusers_views.obtain_auth_token, name="mobile-login"),
    url(r'^' + 'mobile/', include('mobile.urls', namespace="mobile")),
    # the captcha app
    url(r'^captcha/', include('captcha.urls')),

    # support
    # TODO


    #
    # locking the screen (session, actually)
    # this must work on any page except index (and the unlock view, of course)
    #
    # lock (sets request.session['locked'] = True)
    url(r'^lock-session/$', web_views.lock_session, name='lock_session'),
    # the page that shows up when a user is logged in but the session is locked
    # this is only shown when visiting static pages (management) with locked session
    # unlocking will redirect to the page that the user wanted to visit
    url(r'^locked-session/$', web_views.locked_session, name='locked_session'),
    # unlocking
    url(r'^unlock-session/$', web_views.unlock_session, name='unlock_session'),

    # web: everything that happens before user enters a specific company
    url(r'^', include('web.urls', namespace='web')),
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

