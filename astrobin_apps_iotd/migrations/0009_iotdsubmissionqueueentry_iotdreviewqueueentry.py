# Generated by Django 2.2.24 on 2022-01-01 20:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('astrobin_apps_iotd', '0008_iotdjudgementqueueentry'),
    ]

    operations = [
        migrations.CreateModel(
            name='IotdSubmissionQueueEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('published', models.DateTimeField()),
                ('image', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='submission_queue_entries',
                    to='astrobin.Image'
                )),
                ('submitter', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='submission_queue_entries',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'ordering': ('published',),
                'unique_together': {('submitter', 'image')},
            },
        ),

        migrations.CreateModel(
            name='IotdReviewQueueEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_submission_timestamp', models.DateTimeField()),
                ('image', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='review_queue_entries',
                    to='astrobin.Image'
                )),
                ('reviewer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='review_queue_entries',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'ordering': ('last_submission_timestamp',),
                'unique_together': {('reviewer', 'image')},
            },
        ),
    ]
