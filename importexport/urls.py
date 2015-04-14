from django.conf.urls import patterns, url
from django.utils.translation import ugettext as _

from common import globals as g

import views

urlpatterns = patterns('',
    # save terminal settings (will width and such)
    url(r'/import/$', views.import_xls, name='import_xls'),
)
