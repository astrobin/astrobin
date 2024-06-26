# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-11-13 13:09


from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0076_add_userprofile_banned_from_competitions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='exclude_from_competitions',
            field=models.BooleanField(default=False,
                                      help_text='Check this box to be excluded from competitions and contests, such as the Image of the Day, the Top Picks, other custom contests. This will remove you from the leaderboards and hide your Image Index and Contribution Index.',
                                      verbose_name='I want to be excluded from competitions'),
        ),
    ]
