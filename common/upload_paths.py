import uuid
from datetime import date


def upload_path(prefix: str, user_pk: int, filename: str) -> str:
    ext = filename.split('.')[-1]
    return "%s/%d/%d/%s%s.%s" % (
        prefix,
        user_pk,
        date.today().year,
        uuid.uuid4(),
        '-placeholder' if filename == 'astrobin-video-placeholder.jpg' else '',
        ext
    )


def image_upload_path(instance, filename: str) -> str:
    user = instance.user if instance._meta.model_name == 'image' else instance.image.user
    return upload_path('images', user.pk, filename)


def video_upload_path(instance, filename: str) -> str:
    user = instance.user if instance._meta.model_name == 'image' else instance.image.user
    return upload_path('videos', user.pk, filename)


def data_download_upload_path(instance, filename: str) -> str:
    return "data-download/{}/{}".format(
        instance.user.pk,
        'astrobin_data_{}_{}.zip'.format(
            instance.user.username,
            instance.created.strftime('%Y-%m-%d-%H-%M')
        )
    )


def uncompressed_source_upload_path(instance, filename: str) -> str:
    user = instance.user if instance._meta.model_name == 'image' else instance.image.user
    return upload_path('uncompressed', user.pk, filename)


def marketplace_listing_upload_path(instance, filename: str) -> str:
    user = instance.user
    return upload_path('marketplace', user.pk, filename)

