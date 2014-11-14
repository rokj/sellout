# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0004_auto_20141104_1228'),
    ]

    operations = [
        migrations.RenameField(
            model_name='billitem',
            old_name='discount_absolute',
            new_name='discount',
        ),
        migrations.RenameField(
            model_name='billitem',
            old_name='tax_absolute',
            new_name='tax',
        ),
        migrations.RenameField(
            model_name='billitem',
            old_name='tax_percent',
            new_name='tax_rate',
        ),
        migrations.RemoveField(
            model_name='billitem',
            name='base_price',
        ),
        migrations.AddField(
            model_name='billitem',
            name='base',
            field=models.DecimalField(default=None, verbose_name='Base price (for single item), without tax and discounts', max_digits=24, decimal_places=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billitem',
            name='batch',
            field=models.DecimalField(default=None, verbose_name='Base price, multiplied by quantity', max_digits=24, decimal_places=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billitem',
            name='net',
            field=models.DecimalField(default=None, verbose_name='Base price minus discounts', max_digits=24, decimal_places=8),
            preserve_default=False,
        ),
    ]
