# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0003_auto_20141128_1710'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='deleted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='billcompany',
            name='tax_payer',
            field=models.BooleanField(default=False, verbose_name='Tax payer'),
        ),
        migrations.AlterField(
            model_name='company',
            name='tax_payer',
            field=models.BooleanField(default=False, verbose_name='Tax payer'),
        ),
    ]
