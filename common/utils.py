import uuid
from datetime import date


def upload_path(prefix, user_pk, filename):
    ext = filename.split('.')[-1]
    return "%s/%d/%d/%s.%s" % (prefix, user_pk, date.today().year, uuid.uuid4(), ext)
