import uuid
from datetime import date


def upload_path(prefix, user_pk, filename):
    ext = filename.split('.')[-1]
    return "%s/%d/%d/%s.%s" % (prefix, user_pk, date.today().year, uuid.uuid4(), ext)


def image_upload_path(instance, filename):
    user = instance.user if instance._meta.model_name == u'image' else instance.image.user
    return upload_path('images', user.pk, filename)


def data_download_upload_path(instance, filename):
    # type: (DataDownloadRequest, str) -> str
    return "data-download/{}/{}".format(
        instance.user.pk,
        'astrobin_data_{}_{}.zip'.format(
            instance.user.username,
            instance.created.strftime('%Y-%m-%d-%H-%M')))


def uncompressed_source_upload_path(instance, filename):
    user = instance.user if instance._meta.model_name == u'image' else instance.image.user
    return upload_path('uncompressed', user.pk, filename)

