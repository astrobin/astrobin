# Generated by Django 2.2.24 on 2023-06-25 19:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin_apps_equipment', '0113_add_maksutov_newtonian_telescope_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessory',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_accessory_equipment_item',
                related_query_name='is_astrobin_apps_equipment_accessory', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='accessoryeditproposal',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_accessoryeditproposal_equipment_item',
                related_query_name='is_astrobin_apps_equipment_accessoryeditproposal', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='camera',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_camera_equipment_item',
                related_query_name='is_astrobin_apps_equipment_camera', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='cameraeditproposal',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_cameraeditproposal_equipment_item',
                related_query_name='is_astrobin_apps_equipment_cameraeditproposal', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='filter',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_filter_equipment_item',
                related_query_name='is_astrobin_apps_equipment_filter', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='filtereditproposal',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_filtereditproposal_equipment_item',
                related_query_name='is_astrobin_apps_equipment_filtereditproposal', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='mount',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_mount_equipment_item',
                related_query_name='is_astrobin_apps_equipment_mount', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='mounteditproposal',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_mounteditproposal_equipment_item',
                related_query_name='is_astrobin_apps_equipment_mounteditproposal', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_sensor_equipment_item',
                related_query_name='is_astrobin_apps_equipment_sensor', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='sensoreditproposal',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_sensoreditproposal_equipment_item',
                related_query_name='is_astrobin_apps_equipment_sensoreditproposal', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='software',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_software_equipment_item',
                related_query_name='is_astrobin_apps_equipment_software', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='softwareeditproposal',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_softwareeditproposal_equipment_item',
                related_query_name='is_astrobin_apps_equipment_softwareeditproposal', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='telescope',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_telescope_equipment_item',
                related_query_name='is_astrobin_apps_equipment_telescope', to='pybb.Forum'
            ),
        ),
        migrations.AlterField(
            model_name='telescopeeditproposal',
            name='forum',
            field=models.OneToOneField(
                blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_telescopeeditproposal_equipment_item',
                related_query_name='is_astrobin_apps_equipment_telescopeeditproposal', to='pybb.Forum'
            ),
        ),
    ]
