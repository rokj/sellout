# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sync', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sync',
            name='action',
            field=models.CharField(default='save', max_length=20),
            preserve_default=False,
        ),
    ]
