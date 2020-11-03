import random
import string
from datetime import timedelta, date

from django.contrib.auth.models import User, Group
from subscription.models import Subscription, UserSubscription

from astrobin.models import Image, ImageRevision, Telescope, Mount


class Generators:
    def __init__(self):
        pass

    @staticmethod
    def randomString(stringLength=10):
        return ''.join(random.choice(string.ascii_lowercase) for i in range(stringLength))

    @staticmethod
    def user(**kwargs):
        user = User.objects.create_user(
            email=kwargs.pop('email', "%s@%s.com" % (Generators.randomString(), Generators.randomString())),
            username=kwargs.pop('username', Generators.randomString()),
            password=kwargs.pop('password', 'password')
        )

        group_names = kwargs.pop('groups', [])

        for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)
            group.user_set.add(user)

        return user

    @staticmethod
    def image(*args, **kwargs):
        return Image.objects.create(
            user=kwargs.pop('user', Generators.user()),
            is_wip=kwargs.pop('is_wip', False),
            is_final=kwargs.pop('is_final', True),
            corrupted=kwargs.pop('corrupted', False),
            recovered=kwargs.pop('recovered', None),
        )

    @staticmethod
    def imageRevision(*args, **kwargs):
        image = kwargs.pop('image', None)
        if image is None:
            image = Generators.image()

        return ImageRevision.objects.create(
            image=image,
            is_final=kwargs.pop('is_final', False),
            corrupted=kwargs.pop('corrupted', False),
            label=kwargs.pop('label', 'B'),
            description=kwargs.pop('description', None),
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
    def mount():
        return Mount.objects.create(
            make="Brand XYZ",
            name="Mount Pro 1000",
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

        try:
            s = Subscription.objects.get(name=name)
        except Subscription.DoesNotExist:
            s, created = Subscription.objects.get_or_create(
                name=name,
                price=1,
                group=g,
                category="premium_autorenew" if "autorenew" in name else "premium")

        us, created = UserSubscription.objects.get_or_create(
            user=user,
            subscription=s,
            expires=date.today() + timedelta(days=1))
        us.subscribe()

        return us
