import uuid
from datetime import date
from os.path import dirname, abspath


def upload_path(prefix, user_pk, filename):
    ext = filename.split('.')[-1]
    return "%s/%d/%d/%s.%s" % (prefix, user_pk, date.today().year, uuid.uuid4(), ext)


def get_project_root():
    # type: () -> str
    return dirname(dirname(abspath(__file__)))
