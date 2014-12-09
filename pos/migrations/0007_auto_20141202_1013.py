# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0006_bill_currency'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='register',
            unique_together=set([]),
        ),
    ]
