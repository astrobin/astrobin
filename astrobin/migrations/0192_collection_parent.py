# Generated by Django 2.2.24 on 2024-01-17 22:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0191_add_skip_activity_stream_fields_to_image_and_imagerevision'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='parent',
            field=models.ForeignKey(
                blank=True, help_text='If you want to create a nested collection, select the parent collection here.',
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children',
                to='astrobin.Collection', verbose_name='Parent collection'
            ),
        ),
    ]
