# Generated by Django 2.2.24 on 2022-06-25 15:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('astrobin_apps_equipment', '0081_fix_unique_constraint_of_deep_sky_acquisition_migration_record'),
    ]

    operations = [
        migrations.AddField(
            model_name='accessory',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_accessory_edit_proposal_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='accessory',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='accessory',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_accessory_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='accessory',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='accessoryeditproposal',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_accessoryeditproposal_edit_proposal_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='accessoryeditproposal',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='accessoryeditproposal',
            name='edit_proposal_review_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_accessoryeditproposal_edit_proposal_review_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='accessoryeditproposal',
            name='edit_proposal_review_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='accessoryeditproposal',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_accessoryeditproposal_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='accessoryeditproposal',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='camera',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_camera_edit_proposal_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='camera',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='camera',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_camera_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='camera',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cameraeditproposal',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_cameraeditproposal_edit_proposal_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='cameraeditproposal',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cameraeditproposal',
            name='edit_proposal_review_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_cameraeditproposal_edit_proposal_review_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='cameraeditproposal',
            name='edit_proposal_review_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cameraeditproposal',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_cameraeditproposal_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='cameraeditproposal',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='filter',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_filter_edit_proposal_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='filter',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='filter',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_filter_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='filter',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='filtereditproposal',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_filtereditproposal_edit_proposal_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='filtereditproposal',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='filtereditproposal',
            name='edit_proposal_review_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_filtereditproposal_edit_proposal_review_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='filtereditproposal',
            name='edit_proposal_review_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='filtereditproposal',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_filtereditproposal_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='filtereditproposal',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mount',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_mount_edit_proposal_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='mount',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mount',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_mount_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='mount',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mounteditproposal',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_mounteditproposal_edit_proposal_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='mounteditproposal',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mounteditproposal',
            name='edit_proposal_review_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_mounteditproposal_edit_proposal_review_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='mounteditproposal',
            name='edit_proposal_review_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mounteditproposal',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_mounteditproposal_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='mounteditproposal',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sensor',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_sensor_edit_proposal_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='sensor',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sensor',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_sensor_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='sensor',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sensoreditproposal',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_sensoreditproposal_edit_proposal_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='sensoreditproposal',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sensoreditproposal',
            name='edit_proposal_review_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_sensoreditproposal_edit_proposal_review_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='sensoreditproposal',
            name='edit_proposal_review_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sensoreditproposal',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_sensoreditproposal_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='sensoreditproposal',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='software',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_software_edit_proposal_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='software',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='software',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_software_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='software',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='softwareeditproposal',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_softwareeditproposal_edit_proposal_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='softwareeditproposal',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='softwareeditproposal',
            name='edit_proposal_review_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_softwareeditproposal_edit_proposal_review_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='softwareeditproposal',
            name='edit_proposal_review_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='softwareeditproposal',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_softwareeditproposal_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='softwareeditproposal',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='telescope',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_telescope_edit_proposal_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='telescope',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='telescope',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_telescope_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='telescope',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='telescopeeditproposal',
            name='edit_proposal_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_telescopeeditproposal_edit_proposal_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='telescopeeditproposal',
            name='edit_proposal_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='telescopeeditproposal',
            name='edit_proposal_review_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_telescopeeditproposal_edit_proposal_review_locks',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='telescopeeditproposal',
            name='edit_proposal_review_lock_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='telescopeeditproposal',
            name='reviewer_lock',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='astrobin_apps_equipment_telescopeeditproposal_reviewer_locks', to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='telescopeeditproposal',
            name='reviewer_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]