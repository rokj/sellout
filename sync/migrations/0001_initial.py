# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sync',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(max_length=20)),
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
