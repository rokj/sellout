# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='billcompany',
            name='tax_payer',
            field=models.BooleanField(default=True, verbose_name='Tax payer'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='company',
            name='tax_payer',
            field=models.BooleanField(default=True, verbose_name='Tax payer'),
            preserve_default=False,
        ),
    ]
