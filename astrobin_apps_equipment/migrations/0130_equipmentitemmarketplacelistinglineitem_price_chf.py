# Generated by Django 2.2.24 on 2024-01-29 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0129_create_db_extensions_for_distance'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentitemmarketplacelistinglineitem',
            name='price_chf',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
