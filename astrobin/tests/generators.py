import random
import string
from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from pybb.models import Category, Forum, Post, Topic
from subscription.models import Subscription, UserSubscription

from astrobin.enums import SubjectType
from astrobin.enums.display_image_download_menu import DownloadLimitation
from astrobin.models import (
    Accessory, Camera, Collection, Filter, FocalReducer, Image, ImageRevision, Mount, Software, Telescope,
)
from toggleproperties.models import ToggleProperty


class Generators:
    def __init__(self):
        pass

    @staticmethod
    def randomString(stringLength=10):
        return ''.join(random.choice(string.ascii_lowercase) for i in range(stringLength))

    @staticmethod
    def user(**kwargs) -> User:
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
            title=kwargs.pop('title', Generators.randomString()),
            image_file=kwargs.pop('image_file', 'images/foo.jpg'),
            is_wip=kwargs.pop('is_wip', False),
            is_final=kwargs.pop('is_final', True),
            description=kwargs.pop('description', None),
            description_bbcode=kwargs.pop('description_bbcode', None),
            download_limitation=kwargs.pop('download_limitations', DownloadLimitation.ME_ONLY),
            subject_type=kwargs.pop('subject_type', SubjectType.DEEP_SKY),
            published=kwargs.pop('published', None),
        )

    @staticmethod
    def imageRevision(*args, **kwargs):
        image = kwargs.pop('image', None)
        if image is None:
            image = Generators.image()

        return ImageRevision.objects.create(
            image=image,
            image_file=kwargs.pop('image_file', 'images/foo.jpg'),
            is_final=kwargs.pop('is_final', False),
            label=kwargs.pop('label', 'B'),
            title=kwargs.pop('title', None),
            description=kwargs.pop('description', None),
        )

    @staticmethod
    def telescope(*args, **kwargs):
        return Telescope.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Telescope 100/1000'),
            aperture=kwargs.pop('aperture', 100),
            focal_length=kwargs.pop('focal_length', 1000),
            type=kwargs.pop('type', 'REFR_ACHRO'),
        )

    @staticmethod
    def camera(*args, **kwargs):
        return Camera.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Camera 123 Pro'),
            pixel_size=kwargs.pop('pixel_size', 4),
            sensor_width=kwargs.pop('sensor_width', 4),
            sensor_height=kwargs.pop('sensor_height', 4),
            type=kwargs.pop('type', 'CCD'),
        )

    @staticmethod
    def mount(*args, **kwargs):
        return Mount.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Mount Pro 1000'),
            max_payload=kwargs.pop('max_payload', 40),
            pe=kwargs.pop('pe', 1),
        )

    @staticmethod
    def focal_reducer(*args, **kwargs):
        return FocalReducer.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Focal Reducer 0.75x'),
        )

    @staticmethod
    def filter(*args, **kwargs):
        return Filter.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Luminance'),
            type=kwargs.pop('type', 'CLEAR_OR_COLOR'),
            bandwidth=kwargs.pop('bandwidth', 30),
        )

    @staticmethod
    def accessory(*args, **kwargs):
        return Accessory.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Accessory 123'),
        )

    @staticmethod
    def software(*args, **kwargs):
        return Software.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Software 123'),
            type=kwargs.pop('type', 'OPEN_SOURCE_OR_FREEWARE'),
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

    @staticmethod
    def forum_category(**kwargs):
        return Category.objects.create(
            name=kwargs.pop('name', Generators.randomString()),
            slug=kwargs.pop('slug', Generators.randomString())
        )

    @staticmethod
    def forum(**kwargs):
        return Forum.objects.create(
            category=kwargs.pop('category', Generators.forum_category()),
            name=kwargs.pop('name', Generators.randomString()),
        )

    @staticmethod
    def forum_topic(**kwargs):
        return Topic.objects.create(
            forum=kwargs.pop('forum', Generators.forum()),
            name=kwargs.pop('name', Generators.randomString()),
            user=kwargs.pop('user', Generators.user()),
            on_moderation=kwargs.pop('on_moderation', False),
        )

    @staticmethod
    def forum_post(**kwargs):
        user = kwargs.pop('user', Generators.user())

        return Post.objects.create(
            topic=kwargs.pop('topic', Generators.forum_topic(user=user)),
            user=kwargs.pop('user', user),
            body=kwargs.pop('body', Generators.randomString(150)),
            on_moderation=kwargs.pop('on_moderation', False),
        )

    @staticmethod
    def like(target, **kwargs):
        return ToggleProperty.objects.create_toggleproperty(
            'like', target, kwargs.pop('user', Generators.user()))

    @staticmethod
    def collection(**kwargs):
        return Collection.objects.create(
            user=kwargs.pop('user', Generators.user()),
            name=kwargs.pop('name', Generators.randomString()),
        )
