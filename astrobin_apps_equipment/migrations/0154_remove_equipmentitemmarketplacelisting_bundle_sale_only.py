# Generated by Django 2.2.24 on 2024-06-15 20:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0153_add_unique_constraints_to_marketplace_offers'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipmentitemmarketplacelisting',
            name='bundle_sale_only',
        ),
    ]