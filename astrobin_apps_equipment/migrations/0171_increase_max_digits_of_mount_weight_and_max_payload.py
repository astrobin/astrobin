# Generated by Django 2.2.24 on 2024-12-03 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0170_add_thumbnail_to_equipment_preset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mount',
            name='max_payload',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Payload (kg)'
            ),
        ),
        migrations.AlterField(
            model_name='mount',
            name='weight',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Weight (kg)'
            ),
        ),
        migrations.AlterField(
            model_name='mounteditproposal',
            name='max_payload',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Payload (kg)'
            ),
        ),
        migrations.AlterField(
            model_name='mounteditproposal',
            name='weight',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Weight (kg)'
            ),
        ),
    ]
