# Generated by Django 2.2.24 on 2024-02-12 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0193_add_counts_to_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='contribution_index',
            field=models.DecimalField(blank=True, decimal_places=2, editable=False, max_digits=5, null=True),
        ),
    ]
