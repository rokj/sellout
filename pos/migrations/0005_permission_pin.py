# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0004_auto_20141201_1217'),
    ]

    operations = [
        migrations.AddField(
            model_name='permission',
            name='pin',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
    ]
