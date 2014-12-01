# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_auto_20141128_1416'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billcompany',
            name='street',
            field=models.CharField(max_length=200, null=True, verbose_name='Street address', blank=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='street',
            field=models.CharField(max_length=200, null=True, verbose_name='Street address', blank=True),
        ),
    ]
