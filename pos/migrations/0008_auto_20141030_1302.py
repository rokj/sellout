# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0007_auto_20141030_1211'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billcontact',
            name='company',
        ),
        migrations.RemoveField(
            model_name='billregister',
            name='company',
        ),
        migrations.AddField(
            model_name='billcontact',
            name='contact',
            field=models.ForeignKey(default=-1, to='pos.Contact'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='billregister',
            name='contact',
            field=models.ForeignKey(default=-1, to='pos.Contact'),
            preserve_default=False,
        ),
    ]
