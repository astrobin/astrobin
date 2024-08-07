# Generated by Django 2.2.24 on 2024-06-26 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0160_make_marketplace_feedback_relate_to_listing'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipmentitemmarketplacelistinglineitem',
            name='rate_buyer_reminder_sent',
        ),
        migrations.RemoveField(
            model_name='equipmentitemmarketplacelistinglineitem',
            name='rate_seller_reminder_sent',
        ),
        migrations.AddField(
            model_name='equipmentitemmarketplacelisting',
            name='rate_buyer_reminder_sent',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='equipmentitemmarketplacelisting',
            name='rate_seller_reminder_sent',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
