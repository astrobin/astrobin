# Generated by Django 2.2.24 on 2025-04-04 06:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0171_increase_max_digits_of_mount_weight_and_max_payload'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentitemlisting',
            name='image_url',
            field=models.URLField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='equipmentitemlisting',
            name='listing_type',
            field=models.CharField(
                choices=[('SELLS', 'Sells'), ('PAIRS_WELL', 'Pairs well')], default='SELLS', max_length=16
            ),
        ),
    ]
