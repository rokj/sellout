# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0005_auto_20141110_1301'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='sub_total',
            new_name='base',
        ),
        migrations.AddField(
            model_name='bill',
            name='discount_amount',
            field=models.DecimalField(null=True, verbose_name='Discount on the whole bill (absolute or percent)', max_digits=24, decimal_places=8, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bill',
            name='discount',
            field=models.DecimalField(null=True, verbose_name='Discount, sum of all discounts', max_digits=24, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='tax',
            field=models.DecimalField(null=True, verbose_name="Tax amount, absolute value, sum of all items' taxes", max_digits=24, decimal_places=8, blank=True),
        ),
    ]
