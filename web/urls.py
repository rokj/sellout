from django.conf.urls import patterns, url
import views
from pos.views.manage import company

urlpatterns = patterns('',
    # user registrations
    url(r'^sign-up/$', views.sign_up, name='sign_up'),

    # company registration
    url(r'^register-company/$', company.register_company, name='register_company'),
    url(r'^url-name-suggestions$', company.url_name_suggestions, name='url_name_suggestions'),

    url(r'^logout/$', views.logout, name="logout"),

    # registration: passwords, activations, etc.
    url(r'^activate-account/key=(?P<key>[\w]+)$', views.activate_account, name='activate_account'),
    url(r'^lost-password/$', views.lost_password, name='lost_password'),
    url(r'^recover-password/key=(?P<key>[\w]{15})$', views.recover_password, name='recover_password'),

    # actions: invitations, ...
    url(r'^accept-invitation/reference=(?P<reference>[\w]+)$', views.accept_invitation, name='accept_invitation'),
    url(r'^decline-invitation/reference=(?P<reference>[\w]+)$', views.decline_invitation, name='decline_invitation'),

    # companies
    url(r'^select-company/$', views.select_company, name='select_company'),

    # user settings etc.
    url(r'^select-company/$', views.select_company, name='select_company'),
    url(r'^user-profile/$', views.user_profile, name='user_profile'),
    url(r'^select-company/$', views.select_company, name='select_company'),

    url(r'^supported-hardware/$', views.supported_hardware, name='supported-hardware'),

    url(r'^send-contact-message', views.send_contact_message, name='send-contact-message'),

    # index
    url(r'^$', views.index, name='index'),
)