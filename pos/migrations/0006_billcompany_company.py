# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0005_auto_20141029_1528'),
    ]

    operations = [
        migrations.AddField(
            model_name='billcompany',
            name='company',
            field=models.ForeignKey(default=-1, to='pos.Company'),
            preserve_default=False,
        ),
    ]
