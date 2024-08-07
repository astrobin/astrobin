# Generated by Django 2.2.24 on 2022-04-30 13:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin_apps_equipment', '0045_add_equipment_brand_listing_brand_related_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='camera',
            name='back_focus',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Back focus (mm)'
            ),
        ),
        migrations.AlterField(
            model_name='camera',
            name='cooled',
            field=models.BooleanField(default=False, verbose_name='Cooled'),
        ),
        migrations.AlterField(
            model_name='camera',
            name='max_cooling',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Max. cooling (C)'),
        ),
        migrations.AlterField(
            model_name='cameraeditproposal',
            name='back_focus',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Back focus (mm)'
            ),
        ),
        migrations.AlterField(
            model_name='cameraeditproposal',
            name='cooled',
            field=models.BooleanField(default=False, verbose_name='Cooled'),
        ),
        migrations.AlterField(
            model_name='cameraeditproposal',
            name='max_cooling',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Max. cooling (C)'),
        ),
    ]
