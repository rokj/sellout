from django.conf.urls import patterns, url

from payment import views

urlpatterns = patterns('',
    url(r'^pay/$', views.pay, name='pay'),
    url(r'^cancel/(?P<payment>[\d]+)/$', views.cancel_payment, name='cancel'),
    url(r'^info/(?P<payment>[\d]+)/$', views.payment_info, name='payment_info'),
    url(r'^paypal-payment-authorized/(?P<transaction_reference>[0-9a-zA-Z]+)/$', views.paypal_return_url,
        name='paypal_return_url'),
    url(r'^paypal-payment-canceled/(?P<transaction_reference>[0-9a-zA-Z]+)/$', views.paypal_cancel_url,
        name='paypal_cancel_url'),
    url(r'^invoice/(?P<payment>[\d]+)/$', views.invoice, name='invoice'),
)