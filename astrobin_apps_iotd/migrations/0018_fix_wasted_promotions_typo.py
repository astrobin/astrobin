# Generated by Django 2.2.24 on 2023-11-07 11:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_iotd', '0017_add_and_rename_some_iotd_staff_member_score_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='iotdstaffmemberscore',
            old_name='wasted_promotion',
            new_name='wasted_promotions',
        ),
    ]