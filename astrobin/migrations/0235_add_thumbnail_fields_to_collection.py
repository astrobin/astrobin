# Generated by Django 2.2.24 on 2025-03-29 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0234_default_enable_new_gallery_experience_to_true'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='cover_thumbnail',
            field=models.CharField(blank=True, editable=False, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='cover_thumbnail_hd',
            field=models.CharField(blank=True, editable=False, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='w',
            field=models.PositiveSmallIntegerField(blank=True, default=0, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='h',
            field=models.PositiveSmallIntegerField(blank=True, default=0, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='square_cropping',
            field=models.CharField(blank=True, editable=False, max_length=32, null=True),
        ),
    ]
