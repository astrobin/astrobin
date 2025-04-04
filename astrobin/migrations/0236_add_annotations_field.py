from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0235_add_thumbnail_fields_to_collection'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='annotations',
            field=models.TextField(
                blank=True,
                help_text='Annotation data for this image. This data can be used to display markers, labels, or other interactive elements on the image.',
                null=True, verbose_name='Annotations'
            ),
        ),
        migrations.AddField(
            model_name='imagerevision',
            name='annotations',
            field=models.TextField(
                blank=True,
                help_text='Annotation data for this revision. This data can be used to display markers, labels, or other interactive elements on the image.',
                null=True, verbose_name='Annotations'
            ),
        ),
    ]
