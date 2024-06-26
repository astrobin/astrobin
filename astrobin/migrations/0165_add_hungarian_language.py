# Generated by Django 2.2.24 on 2022-11-08 12:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0164_add_utah_desert_remote_observatories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='language',
            field=models.CharField(blank=True,
                choices=[('en', 'English (US)'), ('en-GB', 'English (GB)'), ('it', 'Italian'), ('es', 'Spanish'),
                         ('fr', 'French'), ('fi', 'Finnish'), ('de', 'German'), ('nl', 'Dutch'), ('tr', 'Turkish'),
                         ('sq', 'Albanian'), ('pl', 'Polish'), ('pt', 'Portuguese'), ('el', 'Greek'),
                         ('uk', 'Ukrainian'), ('ru', 'Russian'), ('ar', 'Arabic'), ('ja', 'Japanese'),
                         ('zh-hans', 'Chinese (Simplified)'), ('hu', 'Hungarian')], max_length=8, null=True,
                verbose_name='Language'
            ),
        ),
    ]
