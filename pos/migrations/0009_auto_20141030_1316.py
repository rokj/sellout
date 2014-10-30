# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0008_auto_20141030_1302'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billregister',
            name='contact',
        ),
        migrations.AddField(
            model_name='billregister',
            name='register',
            field=models.ForeignKey(default=-1, to='pos.Register'),
            preserve_default=False,
        ),
    ]
