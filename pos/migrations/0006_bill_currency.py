# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0005_permission_pin'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='currency',
            field=models.CharField(default='\u20ac', max_length=4, verbose_name='Currency'),
            preserve_default=False,
        ),
    ]
