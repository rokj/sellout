# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0004_auto_20141104_1228'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='sub_total',
            new_name='base',
        ),
        migrations.RenameField(
            model_name='bill',
            old_name='note',
            new_name='notes',
        ),
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
            model_name='bill',
            name='due_date',
        ),
        migrations.RemoveField(
            model_name='billitem',
            name='base_price',
        ),
        migrations.AddField(
            model_name='bill',
            name='discount_amount',
            field=models.DecimalField(null=True, verbose_name='Discount on the whole bill (absolute or percent)', max_digits=24, decimal_places=8, blank=True),
            preserve_default=True,
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
        migrations.AlterField(
            model_name='bill',
            name='discount',
            field=models.DecimalField(null=True, verbose_name='Discount, sum of all discounts', max_digits=24, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='discount_type',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Type of discount', choices=[(b'Relative', 'Percentage'), (b'Absolute', 'Absolute value')]),
        ),
        migrations.AlterField(
            model_name='bill',
            name='tax',
            field=models.DecimalField(null=True, verbose_name="Tax amount, absolute value, sum of all items' taxes", max_digits=24, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='billitemdiscount',
            name='type',
            field=models.CharField(default=b'Relative', max_length=30, verbose_name='Discount type', choices=[(b'Relative', 'Percentage'), (b'Absolute', 'Absolute value')]),
        ),
        migrations.AlterField(
            model_name='discount',
            name='type',
            field=models.CharField(default=b'Relative', max_length=30, verbose_name='Discount type', choices=[(b'Relative', 'Percentage'), (b'Absolute', 'Absolute value')]),
        ),
    ]
