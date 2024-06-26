# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-09-30 06:11


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0066_add_never_activated_account_reminder_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='display_wip_images_on_public_gallery',
            field=models.NullBooleanField(help_text="Select if you want your Staging Area images, which are unlisted, to appear on your main gallery when you are logged in and looking at your own gallery. If unselected, your Staging Area imagescan be located via the 'View' menu entry on your gallery page.", verbose_name='See your own Staging Area images on your gallery'),
        ),
    ]
