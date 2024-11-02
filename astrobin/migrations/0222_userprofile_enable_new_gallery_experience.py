# Generated by Django 2.2.24 on 2024-10-27 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0221_rename_rockchuck_to_sadr'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='enable_new_gallery_experience',
            field=models.NullBooleanField(
                default=None,
                help_text='Enable the new gallery experience, with improved navigation and a new image viewer. <a href="https://welcome.astrobin.com/blog/introducing-the-new-astrobin-gallery-experience" target="_blank">Learn more</a>',
                verbose_name='Enable new gallery experience'
            ),
        ),
    ]