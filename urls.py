from django.conf.urls import patterns, include, url
from django.contrib import admin

from blusers import views as blusers_views
from payment.views import paypal_ipn_handler
from pos.views.manage.company import mobile_register_company

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^paypal-ipn-handler/$', paypal_ipn_handler, name='paypal-ipn-handler'),  # login function (url not visibles)

    # admin
    url(r'^admin/', include(admin.site.urls)),

    # POS app
    url(r'^pos/', include('pos.urls', namespace='pos')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('webpos',)}),
    
    # MOBILE urls
    url(r'^pos/mobile/', include('mobile.urls', namespace='mobile_pos')),
    url(r'^pos/sync/', include('sync.urls', namespace='sync')),

    # mobile
    url(r'^' + 'mobile-register/$', blusers_views.mobile_register, name="mobile_register"),  # mobile registration
    url(r'^' + 'mobile-login/(?P<backend>[\w-]+)$', blusers_views.obtain_auth_token, name="mobile-login"),
    url(r'^' + 'mobile-register-company/$', mobile_register_company, name="mobile_register_company"),
    url(r'^' + 'mobile/', include('mobile.urls', namespace="mobile")),
    # the captcha app
    url(r'^captcha/', include('captcha.urls')),

    # support
    url(r'^support/', include('support.urls', namespace="support")),

    # blusers
    url(r'^' + 'settings/', include('blusers.urls', namespace="blusers")),

    # web: everything that happens before user enters a specific company
    url(r'^google-login/$', blusers_views.google_login_or_register, name='google-login'),  # login function (url not visibles)

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

