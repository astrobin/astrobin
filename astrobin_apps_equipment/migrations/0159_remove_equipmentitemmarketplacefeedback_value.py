# Generated by Django 2.2.24 on 2024-06-26 10:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0158_refactor_marketplace_feedback'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipmentitemmarketplacefeedback',
            name='value',
        ),
    ]
