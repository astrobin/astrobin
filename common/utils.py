from contextlib import contextmanager
from itertools import islice
from os.path import dirname, abspath

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.transaction import get_connection


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


@contextmanager
def lock_table(model):
    with transaction.atomic():
        cursor = get_connection().cursor()
        cursor.execute(f'LOCK TABLE {model._meta.db_table}')
        try:
            yield
        finally:
            cursor.close()


def get_segregated_reader_database():
    if settings.TESTING:
        return 'default'
    return 'segregated_reader'


def batch(iterable, size=100):
    iterator = iter(iterable)
    for first in iterator:
        yield [first] + list(islice(iterator, size - 1))
