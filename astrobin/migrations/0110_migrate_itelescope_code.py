from django.db import migrations

OLD_VALUE = 'iT'
NEW_VALUE = 'ITELESCO'


def get_images(apps):
    return apps.get_model('astrobin', 'Image').objects.all()


def migrate_itelescope_values(apps, schema_editor):
    get_images(apps).filter(remote_source=OLD_VALUE).update(remote_source=NEW_VALUE)


def reverse_migrate_itelescope_values(apps, schema_editor):
    get_images(apps).filter(remote_source=NEW_VALUE).update(remote_source=OLD_VALUE)


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0109_add_image_description_bbcode'),
    ]

    operations = [
        migrations.RunPython(migrate_itelescope_values, reverse_migrate_itelescope_values),
    ]
