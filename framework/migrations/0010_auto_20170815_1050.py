# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-15 10:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('framework', '0009_utterance_entity_robustness'),
    ]

    operations = [
        migrations.AlterField(
            model_name='utterance',
            name='entity_robustness',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
