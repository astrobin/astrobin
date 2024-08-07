# Generated by Django 2.2.24 on 2022-01-01 11:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0132_add_userprofile_auto_submit_images_to_iotd_tp_process'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='subject_type',
            field=models.CharField(
                choices=[
                    (None, '---------'),
                    ('DEEP_SKY', 'Deep sky object or field'),
                    ('SOLAR_SYSTEM', 'Solar system body or event'),
                    ('WIDE_FIELD', 'Extremely wide field'),
                    ('STAR_TRAILS', 'Star trails'),
                    ('NORTHERN_LIGHTS', 'Northern lights'),
                    ('NOCTILUCENT_CLOUDS', 'Noctilucent clouds'),
                    ('GEAR', 'Gear'),
                    ('OTHER', 'Other')
                ],
                max_length=18, verbose_name='Subject type'
            ),
        ),
    ]
