# Generated by Django 2.2.24 on 2024-02-22 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0199_userprofile_add_wip_and_deleted_counts'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='image_index',
            field=models.DecimalField(blank=True, decimal_places=3, editable=False, max_digits=7, null=True),
        ),
    ]
