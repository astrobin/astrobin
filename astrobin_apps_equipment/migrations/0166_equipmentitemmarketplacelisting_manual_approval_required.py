# Generated by Django 2.2.24 on 2024-07-11 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0165_equipmentitemmarketplacelisting_area_level_1'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentitemmarketplacelisting',
            name='manual_approval_required',
            field=models.BooleanField(default=False),
        ),
    ]
