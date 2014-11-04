# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='contact',
            field=models.ForeignKey(to='pos.BillContact', null=True),
        ),
    ]
