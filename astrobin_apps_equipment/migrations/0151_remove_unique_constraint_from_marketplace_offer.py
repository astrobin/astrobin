# Generated by Django 2.2.24 on 2024-06-05 20:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0150_add_retracted_status_to_marketplace_offer'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='equipmentitemmarketplaceoffer',
            unique_together=set(),
        ),
    ]