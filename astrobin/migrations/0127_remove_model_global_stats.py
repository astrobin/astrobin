# Generated by Django 2.2.24 on 2021-11-18 21:43

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0126_add_field_type_to_image_gear_merge_record'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GlobalStat',
        ),
    ]
