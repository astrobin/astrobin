# Generated by Django 2.2.24 on 2024-07-04 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0164_order_marketplace_listings_by_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentitemmarketplacelisting',
            name='area_level_1',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]