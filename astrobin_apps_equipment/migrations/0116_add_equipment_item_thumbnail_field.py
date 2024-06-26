# Generated by Django 2.2.24 on 2023-12-24 15:21

import astrobin_apps_equipment.models.equipment_item
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0115_add_stock_fields_to_item_listing'),
    ]

    operations = [
        migrations.AddField(
            model_name='accessory',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='accessoryeditproposal',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='camera',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='cameraeditproposal',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='filter',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='filtereditproposal',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='mount',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='mounteditproposal',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='sensor',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='sensoreditproposal',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='software',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='softwareeditproposal',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='telescope',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
        migrations.AddField(
            model_name='telescopeeditproposal',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=astrobin_apps_equipment.models.equipment_item.thumbnail_upload_path),
        ),
    ]
