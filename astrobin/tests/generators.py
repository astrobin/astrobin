import random
import string

from django.contrib.auth.models import User

from astrobin.models import Image, ImageRevision


class Generators:
    def __init__(self):
        pass

    @staticmethod
    def randomString(stringLength=10):
        return ''.join(random.choice(string.ascii_lowercase) for i in range(stringLength))

    @staticmethod
    def user():
        return User.objects.create(
            username=Generators.randomString(),
            password=Generators.randomString()
        )

    @staticmethod
    def image(*args, **kwargs):
        return Image.objects.create(
            user=kwargs.pop('user', Generators.user()),
            is_wip=kwargs.pop('is_wip', False),
            corrupted=kwargs.pop('corrupted', False)
        )

    @staticmethod
    def imageRevision():
        return ImageRevision.objects.create(
            image=Generators.image()
        )
