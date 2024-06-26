# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-11-17 20:59


from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0080_add_uploader_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagerevision',
            name='uploader_expires',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='imagerevision',
            name='uploader_metadata',
            field=models.CharField(blank=True, editable=False, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='imagerevision',
            name='uploader_name',
            field=models.CharField(blank=True, editable=False, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='imagerevision',
            name='uploader_offset',
            field=models.PositiveIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='imagerevision',
            name='uploader_temporary_file_path',
            field=models.CharField(blank=True, editable=False, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='imagerevision',
            name='uploader_upload_length',
            field=models.PositiveIntegerField(blank=True, editable=False, null=True),
        ),
    ]
