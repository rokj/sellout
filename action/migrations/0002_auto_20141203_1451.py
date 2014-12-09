# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0006_bill_currency'),
        ('action', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='action',
            name='_for',
        ),
        migrations.RemoveField(
            model_name='action',
            name='what',
        ),
        migrations.AddField(
            model_name='action',
            name='company',
            field=models.ForeignKey(blank=True, to='pos.Company', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='receiver',
            field=models.EmailField(default='', max_length=75, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='action',
            name='sender',
            field=models.EmailField(default='', max_length=75),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='action',
            name='type',
            field=models.CharField(default='', max_length=100, db_index=True, choices=[(b'invitation', 'Invite'), (b'notification', 'Notification')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='action',
            name='status',
            field=models.CharField(default=b'waiting', max_length=30, choices=[(b'accepted', 'Accpeted'), (b'declined', 'Declined'), (b'waiting', 'Waiting'), (b'canceled', 'Canceled'), (b'seen', 'Seen')]),
        ),
    ]
