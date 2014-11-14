# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0006_auto_20141110_1324'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bill',
            old_name='note',
            new_name='notes',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='due_date',
        ),
        migrations.AlterField(
            model_name='bill',
            name='discount_type',
            field=models.CharField(blank=True, max_length=16, null=True, verbose_name='Type of discount', choices=[(b'Relative', 'Percentage'), (b'Absolute', 'Absolute value')]),
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
