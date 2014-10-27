# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sync',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('model', models.CharField(max_length=20)),
                ('object_id', models.IntegerField()),
                ('seq', models.IntegerField()),
                ('company', models.ForeignKey(to='pos.Company')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
