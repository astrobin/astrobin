# Generated by Django 2.2.24 on 2022-06-03 11:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0154_various_image_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagerevision',
            name='mouse_hover_image',
            field=models.CharField(blank=True, default='SOLUTION', max_length=16, null=True),
        ),
    ]
