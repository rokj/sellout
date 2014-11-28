from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^sign-up/$', views.sign_up, name='sign_up'),
    url(r'^register-company/$', views.sign_up, name='register_company'),

    # TODO: wrong view, this is
    url(r'^logout/$', views.logout, name="logout"),  # registration

    # registration: passwords, activations, etc.
    url(r'^activate-account/key=(?P<key>[\w]+)$', views.activate_account, name='activate_account'),
    url(r'^lost-password/$', views.lost_password, name='lost_password'),

    # actions: invitations, ...
    # TODO

    # selecting
    url(r'^select-company/$', views.select_company, name='select_company'),
)