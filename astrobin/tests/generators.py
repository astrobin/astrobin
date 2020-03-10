import random
import string

from django.contrib.auth.models import User, Group
from subscription.models import Subscription, UserSubscription

from astrobin.models import Image, ImageRevision, Telescope


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

    @staticmethod
    def telescope():
        return Telescope.objects.create(
            make="Brand XYZ",
            name="Telescope 100/1000",
            aperture=100,
            focal_length=1000,
            type="REFR ACHRO",
        )

    @staticmethod
    def premium_subscription(user, name):
        if name == "AstroBin Lite" or name == "AstroBin Lite (autorenew)":
            group_name = "astrobin_lite"

        elif name == "AstroBin Premium" or name == "AstroBin Premium (autorenew)":
            group_name = "astrobin_premium"

        elif name == "AstroBin Lite 2020+":
            group_name = "astrobin_lite_2020"

        elif name == "AstroBin Premium 2020+":
            group_name = "astrobin_premium_2020"

        elif name == "AstroBin Ultimate 2020+":
            group_name = "astrobin_ultimate_2020"

        g, created = Group.objects.get_or_create(name=group_name)
        s, created = Subscription.objects.get_or_create(
            name=name,
            price=1,
            group=g,
            category="premium")
        us, created = UserSubscription.objects.get_or_create(
            user=user,
            subscription=s)
        us.subscribe()

        return us
