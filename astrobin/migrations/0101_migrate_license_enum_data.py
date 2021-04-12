from django.db import migrations

from astrobin.enums.license import License

LICENSE_MIGRATION_MAP = {
    0: License.ALL_RIGHTS_RESERVED,
    1: License.ATTRIBUTION_NON_COMMERCIAL_SHARE_ALIKE,
    2: License.ATTRIBUTION_NON_COMMERCIAL,
    3: License.ATTRIBUTION_NON_COMMERCIAL_NO_DERIVS,
    4: License.ATTRIBUTION,
    5: License.ATTRIBUTION_SHARE_ALIKE,
    6: License.ATTRIBUTION_NO_DERIVS,
}  # type: Dict[int, str]


def get_images(apps):
    # type: (object) -> QuerySet
    return apps.get_model('astrobin', 'Image').objects.all()


def get_user_profiles(apps):
    # type: (object) -> QuerySet
    return apps.get_model('astrobin', 'UserProfile').objects.all()


def migrate_license_values(apps, schema_editor):
    for old_value, new_value in LICENSE_MIGRATION_MAP.iteritems():
        get_images(apps).filter(license=old_value).update(license=new_value)
        get_user_profiles(apps).filter(default_license=old_value).update(default_license=new_value)


def reverse_migrate_license_values(apps, schema_editor):
    for old_value, new_value in LICENSE_MIGRATION_MAP.iteritems():
        get_images(apps).filter(license=new_value).update(license=old_value)
        get_user_profiles(apps).filter(default_license=new_value).update(default_license=old_value)


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0100_migrate_license_enum'),
    ]

    operations = [
        migrations.RunPython(migrate_license_values, reverse_migrate_license_values),
    ]
