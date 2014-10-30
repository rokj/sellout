# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0006_billcompany_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='billcontact',
            name='company',
            field=models.ForeignKey(default=-1, to='pos.Company'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billregister',
            name='company',
            field=models.ForeignKey(default=-1, to='pos.Company'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='bill',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billcompany',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billcompany',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billcontact',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billcontact',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billitem',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billitemdiscount',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billitemdiscount',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billregister',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='billregister',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='company',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='discount',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='discount',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='permission',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='permission',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='price',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='price',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='productdiscount',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='productdiscount',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='purchaseprice',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='purchaseprice',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='register',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='register',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='tax',
            name='datetime_created',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='tax',
            name='datetime_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True),
        ),
    ]
