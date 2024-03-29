# Generated by Django 2.2.24 on 2023-10-16 08:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0178_add_encoding_error_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='skill_level',
            field=models.CharField(blank=True, choices=[('NA', "n/a///I don't define myself as an astrophotographer at this time."), ('BEGINNER', "Beginner///I started out recently and I'm still getting familiar with the hobby."), ('INTERMEDIATE', "Intermediate///I have been doing astrophotography for a while and wouldn't classify myself as a beginner anymore."), ('ADVANCED', 'Advanced///I developed a comprehensive set of skills and master most aspects of astrophotography.'), ('PROFESSIONAL', 'Professional///Astrophotography is my profession or part of my profession.')], help_text='How would you categorize your current skills as an astrophotographer?', max_length=16, null=True, verbose_name='Self-assessed skill level'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='skill_level_updated',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
