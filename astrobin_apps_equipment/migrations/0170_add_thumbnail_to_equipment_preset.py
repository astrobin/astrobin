# Generated by Django 2.2.24 on 2024-11-20 19:01

import astrobin_apps_equipment.models.equipment_preset
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0169_add_description_image_image_count_total_integration_to_equipmentpreset'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentpreset',
            name='thumbnail',
            field=models.ImageField(
                blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_preset.thumbnail_upload_path
            ),
        )
    ]