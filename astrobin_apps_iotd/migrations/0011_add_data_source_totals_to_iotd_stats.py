# Generated by Django 2.2.24 on 2023-06-29 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_iotd', '0010_iotdstats'),
    ]

    operations = [
        migrations.AddField(
            model_name='iotdstats',
            name='total_amateur_hosting_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='iotdstats',
            name='total_backyard_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='iotdstats',
            name='total_mix_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='iotdstats',
            name='total_other_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='iotdstats',
            name='total_own_remote_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='iotdstats',
            name='total_pro_data_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='iotdstats',
            name='total_public_amateur_data_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='iotdstats',
            name='total_traveler_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='iotdstats',
            name='total_unknown_images',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]
