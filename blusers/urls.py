from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    # url(r'^$', views.register, name='register'),
    # url(r'save_last_used_group/$', views.save_last_used_group, name='save_last_used_group'),

    # mobile registration
    # url(r'^mobile-register', views.mobile_register, name='mobile-register'),

    #API
    url(r'api-token-auth/?$', views.obtain_auth_token)
)
