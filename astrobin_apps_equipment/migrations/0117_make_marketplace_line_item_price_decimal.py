# Generated by Django 2.2.24 on 2023-12-11 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0116_add_marketplace_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipmentitemmarketplacelistinglineitem',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]