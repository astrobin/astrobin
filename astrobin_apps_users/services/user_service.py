from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Q
from django.utils import timezone
from pybb.models import Post

from astrobin.models import Image
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty


class UserService:
    user = None  # type: User

    def __init__(self, user):
        # type: (User) -> None
        self.user = user

    @staticmethod
    def corrupted_query():
        # type: () -> Q
        return Q(corrupted=True, is_final=True) | \
               Q(revisions__corrupted=True, revisions__is_final=True, revisions__deleted=None)

    def get_all_images(self):
        # type: () -> QuerySet
        return Image.objects_including_wip.filter(user=self.user)

    def get_corrupted_images(self):
        # type: () -> QuerySet
        return self.get_all_images().filter(UserService.corrupted_query()).distinct()

    def get_recovered_images(self):
        # type: () -> QuerySet
        return Image.all_objects.filter(user=self.user).filter(corrupted=True).exclude(recovered=None)

    def get_public_images(self):
        # type: () -> QuerySet
        return Image.objects.filter(user=self.user)

    def get_wip_images(self):
        # type: () -> QuerySet
        return Image.wip.filter(user=self.user)

    def get_deleted_images(self):
        # type: () -> QuerySet
        return Image.deleted_objects.filter(user=self.user)

    def get_bookmarked_images(self):
        # type: () -> QuerySet
        image_ct = ContentType.objects.get_for_model(Image)  # type: ContentType
        bookmarked_pks = [x.object_id for x in \
                          ToggleProperty.objects.toggleproperties_for_user("bookmark", self.user).filter(
                              content_type=image_ct)
                          ]  # type: List[int]

        return Image.objects \
            .filter(pk__in=bookmarked_pks) \
            .exclude(UserService.corrupted_query())

    def get_liked_images(self):
        # type: () -> QuerySet
        image_ct = ContentType.objects.get_for_model(Image)  # type: ContentType
        liked_pks = [
            x.object_id for x in \
            ToggleProperty.objects.toggleproperties_for_user("like", self.user).filter(content_type=image_ct)
        ]  # type: List[int]

        return Image.objects \
            .filter(pk__in=liked_pks) \
            .exclude(UserService.corrupted_query())

    def get_image_numbers(self, include_corrupted=True):
        public = self.get_public_images()
        if not include_corrupted:
            public = public.exclude(UserService.corrupted_query())

        wip = self.get_wip_images()
        if not include_corrupted:
            wip = wip.exclude(UserService.corrupted_query())

        return {
            'public_images_no': public.count(),
            'wip_images_no': wip.count(),
            'corrupted_no': self.get_corrupted_images().count(),
            'recovered_no': self.get_recovered_images().count(),
            'deleted_images_no': self.get_deleted_images().count(),
        }

    def shadow_bans(self, other):
        # type: (User) -> bool
        return other.userprofile in self.user.userprofile.shadow_bans.all()

    def can_like(self, obj):
        if self.user.is_superuser:
            return True

        index = 0
        min_index_to_like = settings.MIN_INDEX_TO_LIKE

        if self.user.is_authenticated():
            index = self.user.userprofile.get_scores()['user_scores_index']

        if is_free(self.user) and index < min_index_to_like:
            return False

        if obj.__class__.__name__ == 'Image':
            return self.user != obj.user
        elif obj.__class__.__name__ == 'NestedComment':
            return  self.user != obj.author
        elif obj.__class__.__name__ == 'Post':
            return self.user != obj.user

        return False

    def can_unlike(self, obj):
        if not self.user.is_authenticated():
            return False

        property = ToggleProperty.objects.toggleproperties_for_object('like', obj, self.user)  # type: QuerySet
        if property.exists():
            one_hour_ago = timezone.now() - timedelta(hours=1)
            return property.first().created_on > one_hour_ago

        return False

    def get_all_comments(self):
        return NestedComment.objects.filter(author=self.user, deleted=False)

    def get_all_forum_posts(self):
        return Post.objects.filter(user=self.user)

    def received_likes_count(self):
        likes = 0

        for image in self.get_all_images().iterator():
            likes += image.likes()

        for comment in self.get_all_comments().iterator():
            likes += len(comment.likes)

        for post in self.get_all_forum_posts().iterator():
            likes += ToggleProperty.objects.filter(
                object_id=post.pk,
                content_type=ContentType.objects.get_for_model(Post),
                property_type='like'
            ).count()

        return likes
