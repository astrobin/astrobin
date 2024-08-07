# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-10-05 09:17


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0001_initial'),
        ('astrobin', '0067_add_display_wip_images_on_public_gallery'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commercialgear',
            name='image',
        ),
        migrations.RemoveField(
            model_name='commercialgear',
            name='producer',
        ),
        migrations.RemoveField(
            model_name='retailedgear',
            name='retailer',
        ),
        migrations.RemoveField(
            model_name='gear',
            name='commercial',
        ),
        migrations.RemoveField(
            model_name='gear',
            name='retailed',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='company_description',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='company_name',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='company_website',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='retailer_country',
        ),
        migrations.AddField(
            model_name='gear',
            name='equipment_brand_listings',
            field=models.ManyToManyField(editable=False, related_name='gear_items', to='astrobin_apps_equipment.EquipmentBrandListing'),
        ),
        migrations.AddField(
            model_name='gear',
            name='equipment_item_listings',
            field=models.ManyToManyField(editable=False, related_name='gear_items', to='astrobin_apps_equipment.EquipmentItemListing'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='allow_retailer_integration',
            field=models.BooleanField(default=True, help_text="AstroBin may associate with retailers of astronomy and astrophotography equipment to enhance the display of equipment items with links to sponsoring partners. The integration is subtle and non intrusive, and it would help a lot if you didn't disable it. Thank you in advance!", verbose_name='Allow retailer integration'),
        ),
        migrations.DeleteModel(
            name='CommercialGear',
        ),
        migrations.DeleteModel(
            name='RetailedGear',
        ),
    ]
