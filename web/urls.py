from django.conf.urls import patterns, url
import views
from pos.views.manage import company

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),

    # user registrations
    url(r'^sign-up/$', views.sign_up, name='sign_up'),

    # company registration
    url(r'^register-company/$', company.register_company, name='register_company'),
    url(r'^url-name-suggestions$', company.url_name_suggestions, name='url_name_suggestions'),

    # TODO: wrong view, this is
    url(r'^logout/$', views.logout, name="logout"),

    # registration: passwords, activations, etc.
    url(r'^activate-account/key=(?P<key>[\w]+)$', views.activate_account, name='activate_account'),
    url(r'^lost-password/$', views.lost_password, name='lost_password'),

    # actions: invitations, ...
    # TODO

    # selecting
    url(r'^select-company/$', views.select_company, name='select_company'),
)