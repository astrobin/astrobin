from __future__ import unicode_literals

from django.db import migrations


def get_images(apps):
    # type: (object) -> QuerySet
    return apps.get_model('astrobin', 'Image').objects.all()


def migrate_acquisition_type_traditional_values(apps, schema_editor):
    get_images(apps).filter(acquisition_type="TRADITIONAL").update(acquisition_type="REGULAR")


def reverse_migrate_acquisition_type_traditional_values(apps, schema_editor):
    get_images(apps).filter(acquisition_type="REGULAR").update(acquisition_type="TRADITIONAL")


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0086_add_userprofile_last_seen'),
    ]

    operations = [
        migrations.RunPython(
            migrate_acquisition_type_traditional_values,
            reverse_migrate_acquisition_type_traditional_values),
    ]
