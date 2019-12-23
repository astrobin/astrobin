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
    def image():
        return Image.objects.create(
            user=Generators.user()
        )

    @staticmethod
    def imageRevision():
        return ImageRevision.objects.create(
            image=Generators.image()
        )
