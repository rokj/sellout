# -*- coding:utf-8 -*-
import os

import django
django.setup()

from common.functions import send_email

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webpos.settings")

import settings

send_email(settings.EMAIL_FROM, [settings.ADMINS[0][1]], None, "Test message", "message", "message")
