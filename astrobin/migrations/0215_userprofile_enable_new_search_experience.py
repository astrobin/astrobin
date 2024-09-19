# Generated by Django 2.2.24 on 2024-08-26 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0214_imagerevision_constellation'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='enable_new_search_experience',
            field=models.NullBooleanField(default=None, help_text='Enable the new search experience, which includes new filters and a new layout. <a href="https://welcome.astrobin.com/blog/introducing-the-new-astrobin-search-experience" target="_blank">Learn more</a>', verbose_name='Enable new search experience'),
        ),
    ]