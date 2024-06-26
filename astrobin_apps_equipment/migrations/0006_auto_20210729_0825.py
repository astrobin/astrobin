# Generated by Django 2.2.24 on 2021-07-29 08:25

import astrobin_apps_equipment.models.equipment_item
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0005_add_sensor_and_camera'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='camera',
            options={'ordering': ['brand__name', 'name']},
        ),
        migrations.AlterModelOptions(
            name='sensor',
            options={'ordering': ['brand__name', 'name']},
        ),
        migrations.AlterField(
            model_name='camera',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='camera',
            name='image',
            field=models.ImageField(upload_to=astrobin_apps_equipment.models.equipment_item.image_upload_path),
        ),
        migrations.AlterField(
            model_name='camera',
            name='sensor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='cameras', to='astrobin_apps_equipment.Sensor'),
        ),
        migrations.AlterField(
            model_name='camera',
            name='type',
            field=models.CharField(choices=[('CCD', 'CCD'), ('CMOS', 'CMOS'), ('DSLR', 'DSLR'), ('GUIDER/PLANETARY', 'Guider/Planetary'), ('FILM', 'Film'), ('COMPACT', 'Compact'), ('VIDEO', 'Video camera')], max_length=64, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='adc',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='color_or_mono',
            field=models.CharField(blank=True, choices=[('C', 'Color'), ('M', 'Monochromatic')], max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='frame_rate',
            field=models.PositiveSmallIntegerField(blank=True, help_text='FPS', null=True, verbose_name='Frame rate'),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='full_well_capacity',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='image',
            field=models.ImageField(upload_to=astrobin_apps_equipment.models.equipment_item.image_upload_path),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='pixel_size',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='quantum_efficiency',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='read_noise',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='sensor_height',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AlterField(
            model_name='sensor',
            name='sensor_width',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
