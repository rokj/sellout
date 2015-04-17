# -*- coding:utf-8 -*-
import os

import django
django.setup()

from common.functions import send_email

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sellout_biz.settings")
import settings
send_email(settings.EMAIL_FROM, [settings.ADMINS[0][1]], None, "Test message sellout.biz", "message", "message")


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sellout_biz.spletna_blagajna_settings")
import spletna_blagajna_settings as settings
send_email(settings.EMAIL_FROM, [settings.ADMINS[0][1]], None, "Test message from spletna-blagajna.si", "message", "message")
