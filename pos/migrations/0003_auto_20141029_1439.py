# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_auto_20141029_1027'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billhistory',
            name='bill',
        ),
        migrations.RemoveField(
            model_name='billhistory',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='billhistory',
            name='updated_by',
        ),
        migrations.DeleteModel(
            name='BillHistory',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='city',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='company_name',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='country',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='date_of_birth',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='email',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='postcode',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='sex',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='state',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='street_address',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='type',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='user',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='user_name',
        ),
        migrations.RemoveField(
            model_name='bill',
            name='vat',
        ),
        migrations.RemoveField(
            model_name='register',
            name='location',
        ),
        migrations.RemoveField(
            model_name='register',
            name='name',
        ),
        migrations.RemoveField(
            model_name='register',
            name='print_location',
        ),
        migrations.RemoveField(
            model_name='register',
            name='print_logo',
        ),
        migrations.RemoveField(
            model_name='register',
            name='receipt_format',
        ),
        migrations.RemoveField(
            model_name='register',
            name='receipt_type',
        ),
        migrations.AlterField(
            model_name='billitem',
            name='discount_absolute',
            field=models.DecimalField(null=True, verbose_name='Discount, absolute value, sum of all valid discounts on this item', max_digits=16, decimal_places=4, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='price',
            unique_together=None,
        ),
        migrations.AlterUniqueTogether(
            name='purchaseprice',
            unique_together=None,
        ),
    ]
