# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-06-09 13:11


from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0105_add_last_seen_in_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='full_size_display_limitation',
            field=models.CharField(
                blank=True, choices=[
                    ('EVERYBODY', 'Everybody'),
                    ('PAYING', 'Paying members only'),
                    ('MEMBERS', 'Members only'),
                    ('ME', 'Me only'),
                    ('NOBODY', 'Nobody')
                ],
                default=b'EVERYBODY',
                help_text='Specify what user groups are allowed to view this image at its full size.',
                max_length=16,
                null=True,
                verbose_name='Allow full-size display'
            ),
        ),
    ]
