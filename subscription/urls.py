from django.conf.urls import patterns, url

from subscription import views

urlpatterns = patterns('',
    # my subscriptions
    url(r'^$', views.subscriptions, name='subscriptions'),
    url(r'^new/$', views.subscription, name='new'),

)
