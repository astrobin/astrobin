import random
import string
from datetime import date, timedelta
from io import BytesIO

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.utils import timezone
from pybb.models import Category, Forum, Post, Topic
from subscription.models import Subscription, UserSubscription

from astrobin.enums import SubjectType
from astrobin.enums.display_image_download_menu import DownloadLimitation
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.enums.mouse_hover_image import MouseHoverImage
from astrobin.models import (
    Accessory, Camera, Collection, Filter, FocalReducer, GearMigrationStrategy, Image, ImageRevision, Mount, Software,
    Telescope,
)
from astrobin_apps_premium.services.premium_service import SubscriptionName
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
    def pil_image(*args, **kwargs):
        from PIL import Image
        pil_image = Image.new('RGB', (100, 100), 'red')
        image_io = BytesIO()
        pil_image.save(image_io, format='JPEG')
        return ContentFile(image_io.getvalue(), kwargs.pop('filename', 'foo.jpg'))

    @staticmethod
    def image(*args, **kwargs):
        pil_image = kwargs.pop('image_file', Generators.pil_image())
        user = kwargs.pop('user', None)
        if not user:
            user = Generators.user()

        return Image.objects.create(
            user=user,
            title=kwargs.pop('title', Generators.randomString()),
            image_file=pil_image,
            is_wip=kwargs.pop('is_wip', False),
            is_final=kwargs.pop('is_final', True),
            description=kwargs.pop('description', None),
            description_bbcode=kwargs.pop('description_bbcode', None),
            download_limitation=kwargs.pop('download_limitations', DownloadLimitation.ME_ONLY),
            subject_type=kwargs.pop('subject_type', SubjectType.DEEP_SKY),
            published=kwargs.pop('published', None),
            submitted_for_iotd_tp_consideration=kwargs.pop('submitted_for_iotd_tp_consideration', None),
            moderator_decision=kwargs.pop('moderator_decision', ModeratorDecision.UNDECIDED),
        )

    @staticmethod
    def image_revision(*args, **kwargs):
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
            mouse_hover_image=kwargs.pop('mouse_hover_image', MouseHoverImage.SOLUTION),
        )

    @staticmethod
    def telescope(*args, **kwargs) -> Telescope:
        return Telescope.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Telescope 100/1000'),
            aperture=kwargs.pop('aperture', 100),
            focal_length=kwargs.pop('focal_length', 1000),
            type=kwargs.pop('type', 'REFR_ACHRO'),
        )

    @staticmethod
    def camera(*args, **kwargs) -> Camera:
        return Camera.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Camera 123 Pro'),
            pixel_size=kwargs.pop('pixel_size', 4),
            sensor_width=kwargs.pop('sensor_width', 4),
            sensor_height=kwargs.pop('sensor_height', 4),
            type=kwargs.pop('type', 'CCD'),
        )

    @staticmethod
    def mount(*args, **kwargs) -> Mount:
        return Mount.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Mount Pro 1000'),
            max_payload=kwargs.pop('max_payload', 40),
            pe=kwargs.pop('pe', 1),
        )

    @staticmethod
    def focal_reducer(*args, **kwargs) -> FocalReducer:
        return FocalReducer.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Focal Reducer 0.75x'),
        )

    @staticmethod
    def filter(*args, **kwargs) -> Filter:
        return Filter.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Luminance'),
            type=kwargs.pop('type', 'CLEAR_OR_COLOR'),
            bandwidth=kwargs.pop('bandwidth', 30),
        )

    @staticmethod
    def accessory(*args, **kwargs) -> Accessory:
        return Accessory.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Accessory 123'),
        )

    @staticmethod
    def software(*args, **kwargs) -> Software:
        return Software.objects.create(
            make=kwargs.pop('make', 'Brand XYZ'),
            name=kwargs.pop('name', 'Software 123'),
            type=kwargs.pop('type', 'OPEN_SOURCE_OR_FREEWARE'),
        )

    @staticmethod
    def gear_migration_strategy(*args, **kwargs) -> GearMigrationStrategy:
        return GearMigrationStrategy.objects.create(
            gear=kwargs.pop('gear', Generators.telescope()),
            user=kwargs.pop('user', None),
            migration_flag=kwargs.pop('migration_flag', 'WRONG_TYPE'),
            migration_flag_timestamp=kwargs.pop('migration_flag_timestamp', timezone.now()),
            migration_content_object=kwargs.pop('migration_content_object', None),
            migration_flag_moderator=kwargs.pop('migration_flag_moderator', Generators.user()),
            migration_flag_reviewer=kwargs.pop('migration_flag_reviewer', None),
            migration_flag_reviewer_decision=kwargs.pop('migration_flag_reviewer_decision', None),
        )

    @staticmethod
    def premium_subscription(user: User, name: SubscriptionName) -> UserSubscription:
        if name in (SubscriptionName.LITE_CLASSIC, SubscriptionName.LITE_CLASSIC_AUTORENEW):
            group_name = "astrobin_lite"
        elif name in (SubscriptionName.PREMIUM_CLASSIC, SubscriptionName.PREMIUM_CLASSIC_AUTORENEW):
            group_name = "astrobin_premium"
        elif name in (
                SubscriptionName.LITE_2020,
                SubscriptionName.LITE_2020_AUTORENEW_YEARLY,
                SubscriptionName.LITE_2020_AUTORENEW_MONTHLY
        ):
            group_name = "astrobin_lite_2020"
        elif name in (
                SubscriptionName.PREMIUM_2020,
                SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY,
                SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY
        ):
            group_name = "astrobin_premium_2020"
        elif name in (
                SubscriptionName.ULTIMATE_2020,
                SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY,
                SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY
        ):
            group_name = "astrobin_ultimate_2020"
        else:
            raise ValueError(f"Unknown subscription name: {name}")

        group, created = Group.objects.get_or_create(name=group_name)

        try:
            s = Subscription.objects.get(name=name.value)
        except Subscription.DoesNotExist:
            recurrence_unit = None
            recurrence_period = None

            if name in (
                SubscriptionName.LITE_2020_AUTORENEW_MONTHLY,
                SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY,
                SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY,
            ):
                recurrence_unit = 'M'
                recurrence_period = 1
            elif name in (
                SubscriptionName.LITE_2020_AUTORENEW_YEARLY,
                SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY,
                SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY,
                SubscriptionName.LITE_CLASSIC_AUTORENEW,
                SubscriptionName.PREMIUM_CLASSIC_AUTORENEW,
            ):
                recurrence_unit = 'Y'
                recurrence_period = 1

            s, created = Subscription.objects.get_or_create(
                name=name.value,
                price=1,
                group=group,
                category='premium_autorenew' if 'autorenew' in name.value else "premium",
                recurrence_unit=recurrence_unit,
                recurrence_period=recurrence_period,
            )

        user_subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            subscription=s,
            expires=date.today() + timedelta(days=1),
            cancelled=s.recurrence_unit is None,
        )
        user_subscription.subscribe()

        return user_subscription

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
        user = kwargs.pop('user', None)
        if user is None:
            user = Generators.user()

        return ToggleProperty.objects.create_toggleproperty(
            'like', target, user
        )

    @staticmethod
    def follow(target, **kwargs):
        user = kwargs.pop('user', None)
        if user is None:
            user = Generators.user()

        return ToggleProperty.objects.create_toggleproperty(
            'follow', target, user
        )

    @staticmethod
    def collection(**kwargs):
        return Collection.objects.create(
            user=kwargs.pop('user', Generators.user()),
            name=kwargs.pop('name', Generators.randomString()),
        )
