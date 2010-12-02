from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings
import mimetypes
from uuid import uuid4

from models import Image

def store_in_s3(file, uid, bucket):
    conn = S3Connection(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)
    b = conn.create_bucket(bucket)
    k = Key(b)
    k.key = uid
    k.set_metadata("Content-Type", mimetypes.guess_type(file.name)[0])
    k.set_contents_from_string(file.read())
    k.set_acl("public-read")

