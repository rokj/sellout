# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_auto_20141103_1317'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='user_id',
            field=models.IntegerField(default=-1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bill',
            name='user_name',
            field=models.CharField(default='X', max_length=64),
            preserve_default=False,
        ),
    ]
