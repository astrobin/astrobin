# Generated by Django 2.2.24 on 2024-04-14 19:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0203_image_pending_collaborators'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('astrobin_apps_iotd', '0021_add_lanscape_images_to_iotd_stats'),
    ]

    operations = [
        migrations.CreateModel(
            name='IotdReviewerSeenImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='astrobin.Image')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'unique_together': {('user', 'image')},
            },
        ),
    ]