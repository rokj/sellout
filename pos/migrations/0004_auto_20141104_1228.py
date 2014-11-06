# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0003_auto_20141103_1321'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billitem',
            name='single_total',
        ),
        migrations.AlterField(
            model_name='bill',
            name='discount',
            field=models.DecimalField(null=True, verbose_name='Discount on the whole bill (absolute or percent)', max_digits=24, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='sub_total',
            field=models.DecimalField(null=True, verbose_name='Sub total', max_digits=24, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='tax',
            field=models.DecimalField(null=True, verbose_name='Tax amount, absolute value, derived from products', max_digits=24, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='total',
            field=models.DecimalField(null=True, verbose_name='Total amount to be paid', max_digits=24, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='base_price',
            field=models.DecimalField(verbose_name='Base price, without tax and discounts', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='discount_absolute',
            field=models.DecimalField(null=True, verbose_name='Discount, absolute value, sum of all valid discounts on this item', max_digits=24, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='quantity',
            field=models.DecimalField(verbose_name='Quantity', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='stock',
            field=models.DecimalField(verbose_name='Number of items left in stock', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='tax_absolute',
            field=models.DecimalField(verbose_name='Tax amount, absolute value', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='tax_percent',
            field=models.DecimalField(null=True, verbose_name="Tax in percent, copied from product's tax rate", max_digits=11, decimal_places=8, blank=True),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='total',
            field=models.DecimalField(verbose_name='Total price, including taxes, discounts and multiplied by quantity', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='billitemdiscount',
            name='amount',
            field=models.DecimalField(verbose_name='Amount', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='discount',
            name='amount',
            field=models.DecimalField(verbose_name='Amount', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='price',
            name='unit_price',
            field=models.DecimalField(verbose_name='Price per unit, excluding tax', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock',
            field=models.DecimalField(verbose_name='Number of items left in stock', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='purchaseprice',
            name='unit_price',
            field=models.DecimalField(verbose_name='Purchase price per unit, excluding tax', max_digits=24, decimal_places=8),
        ),
        migrations.AlterField(
            model_name='tax',
            name='amount',
            field=models.DecimalField(verbose_name='Tax amount', max_digits=11, decimal_places=8),
        ),
    ]
