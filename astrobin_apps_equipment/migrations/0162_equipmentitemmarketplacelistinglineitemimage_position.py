# Generated by Django 2.2.24 on 2024-07-01 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0161_move_rating_reminders_to_listing_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentitemmarketplacelistinglineitemimage',
            name='position',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
