# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_auto_20150926_2249'),
    ]

    operations = [
        migrations.AddField(
            model_name='billcompany',
            name='tax_payer',
            field=models.CharField(default=b'no', max_length=3, verbose_name='Tax payer', choices=[(b'yes', 'Yes'), (b'no', 'No'), (b'eu', 'EU')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='company',
            name='tax_payer',
            field=models.CharField(default=b'no', max_length=3, verbose_name='Tax payer', choices=[(b'yes', 'Yes'), (b'no', 'No'), (b'eu', 'EU')]),
            preserve_default=True,
        ),
    ]
