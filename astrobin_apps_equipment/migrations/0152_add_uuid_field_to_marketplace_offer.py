# Generated by Django 2.2.24 on 2024-06-06 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0151_remove_unique_constraint_from_marketplace_offer'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentitemmarketplacemasteroffer',
            name='master_offer_uuid',
            field=models.CharField(default='00000000-0000-0000-0000-000000000000', editable=False, max_length=36),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='equipmentitemmarketplaceoffer',
            name='master_offer_uuid',
            field=models.CharField(default='00000000-0000-0000-0000-000000000000', max_length=36),
            preserve_default=False,
        ),
    ]
