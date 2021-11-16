# -*- coding: utf-8 -*-


from django.db import migrations
from django.db.models import F


def migrate_sensor_specification_url_to_website(apps, schema_editor):
    apps.get_model('astrobin_apps_equipment', 'Sensor').objects.filter(specification_url__isnull=False).update(
        website=F('specification_url')
    )


def migrate_sensor_website_to_specification_url(apps, schema_editor):
    apps.get_model('astrobin_apps_equipment', 'Sensor').objects.filter(website__isnull=False).update(
        specification_url=F('website')
    )


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin_apps_equipment', '0036_add_field_website_to_equipment_items'),
    ]

    operations = [
        migrations.RunPython(
            migrate_sensor_specification_url_to_website,
            migrate_sensor_website_to_specification_url
        )
    ]
