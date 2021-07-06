from os.path import dirname, abspath

from django.contrib.auth.models import User


def get_project_root():
    # type: () -> str
    return dirname(dirname(abspath(__file__)))


def get_sentinel_user():
    return User.objects.get_or_create(username='deleted')[0]
