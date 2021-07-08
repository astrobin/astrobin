from os.path import dirname, abspath

from django.contrib.auth.models import User


def get_project_root():
    # type: () -> str
    return dirname(dirname(abspath(__file__)))


def get_sentinel_user():
    return User.objects.get_or_create(username='deleted')[0]


def read_in_chunks(file_object, chunk_size=1024):
    """Lazy function (generator) to read a file piece by piece. Default chunk size: 1k."""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data
