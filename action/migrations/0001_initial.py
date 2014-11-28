# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False, blank=True)),
                ('datetime_updated', models.DateTimeField(default=django.utils.timezone.now, null=True, editable=False, blank=True)),
                ('_for', models.EmailField(max_length=75, verbose_name='For whom', db_index=True)),
                ('what', models.CharField(help_text='Should be just code', max_length=100, verbose_name='For what', db_index=True)),
                ('status', models.CharField(default=b'waiting', max_length=30, verbose_name='Waiting action status', choices=[(b'accepted', 'Accpeted'), (b'declined', 'Declined'), (b'waiting', 'Waiting'), (b'canceled', 'Canceled'), (b'seen', 'Seen')])),
                ('data', models.TextField(verbose_name='Additional data')),
                ('reference', models.CharField(unique=True, max_length=30, verbose_name='Reference for an action')),
                ('created_by', models.ForeignKey(related_name=b'action_action_created_by', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(related_name=b'action_action_updated_by', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
