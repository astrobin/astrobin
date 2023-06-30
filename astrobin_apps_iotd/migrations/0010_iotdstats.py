# Generated by Django 2.2.24 on 2023-06-29 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_iotd', '0009_iotdsubmissionqueueentry_iotdreviewqueueentry'),
    ]

    operations = [
        migrations.CreateModel(
            name='IotdStats',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('days', models.PositiveSmallIntegerField()),
                ('distinct_iotd_winners', models.PositiveIntegerField()),
                ('distinct_tp_winners', models.PositiveIntegerField()),
                ('distinct_tpn_winners', models.PositiveIntegerField()),
                ('total_iotds', models.PositiveIntegerField()),
                ('total_tps', models.PositiveIntegerField()),
                ('total_tpns', models.PositiveIntegerField()),
                ('total_submitted_images', models.PositiveIntegerField()),
                ('total_deep_sky_images', models.PositiveIntegerField()),
                ('total_solar_system_images', models.PositiveIntegerField()),
                ('total_wide_field_images', models.PositiveIntegerField()),
                ('total_star_trails_images', models.PositiveIntegerField()),
                ('total_northern_lights_images', models.PositiveIntegerField()),
                ('total_noctilucent_clouds_images', models.PositiveIntegerField()),
                ('deep_sky_iotds', models.PositiveIntegerField()),
                ('solar_system_iotds', models.PositiveIntegerField()),
                ('wide_field_iotds', models.PositiveIntegerField()),
                ('star_trails_iotds', models.PositiveIntegerField()),
                ('northern_lights_iotds', models.PositiveIntegerField()),
                ('noctilucent_clouds_iotds', models.PositiveIntegerField()),
                ('deep_sky_tps', models.PositiveIntegerField()),
                ('solar_system_tps', models.PositiveIntegerField()),
                ('wide_field_tps', models.PositiveIntegerField()),
                ('star_trails_tps', models.PositiveIntegerField()),
                ('northern_lights_tps', models.PositiveIntegerField()),
                ('noctilucent_clouds_tps', models.PositiveIntegerField()),
                ('deep_sky_tpns', models.PositiveIntegerField()),
                ('solar_system_tpns', models.PositiveIntegerField()),
                ('wide_field_tpns', models.PositiveIntegerField()),
                ('star_trails_tpns', models.PositiveIntegerField()),
                ('northern_lights_tpns', models.PositiveIntegerField()),
                ('noctilucent_clouds_tpns', models.PositiveIntegerField()),
                ('backyard_iotds', models.PositiveIntegerField()),
                ('traveller_iotds', models.PositiveIntegerField()),
                ('own_remote_iotds', models.PositiveIntegerField()),
                ('amateur_hosting_iotds', models.PositiveIntegerField()),
                ('public_amateur_data_iotds', models.PositiveIntegerField()),
                ('pro_data_iotds', models.PositiveIntegerField()),
                ('mix_iotds', models.PositiveIntegerField()),
                ('other_iotds', models.PositiveIntegerField()),
                ('unknown_iotds', models.PositiveIntegerField()),
                ('backyard_tps', models.PositiveIntegerField()),
                ('traveller_tps', models.PositiveIntegerField()),
                ('own_remote_tps', models.PositiveIntegerField()),
                ('amateur_hosting_tps', models.PositiveIntegerField()),
                ('public_amateur_data_tps', models.PositiveIntegerField()),
                ('pro_data_tps', models.PositiveIntegerField()),
                ('mix_tps', models.PositiveIntegerField()),
                ('other_tps', models.PositiveIntegerField()),
                ('unknown_tps', models.PositiveIntegerField()),
                ('backyard_tpns', models.PositiveIntegerField()),
                ('traveller_tpns', models.PositiveIntegerField()),
                ('own_remote_tpns', models.PositiveIntegerField()),
                ('amateur_hosting_tpns', models.PositiveIntegerField()),
                ('public_amateur_data_tpns', models.PositiveIntegerField()),
                ('pro_data_tpns', models.PositiveIntegerField()),
                ('mix_tpns', models.PositiveIntegerField()),
                ('other_tpns', models.PositiveIntegerField()),
                ('unknown_tpns', models.PositiveIntegerField()),
            ],
        ),
    ]