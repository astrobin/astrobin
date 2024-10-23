import logging
import math
from datetime import datetime, timedelta
from typing import List, Optional, Union

import numpy as np
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models import OuterRef, Q, QuerySet, Subquery, Sum
from django.db.models.functions import Length
from django.utils import timezone
from django.utils.translation import ugettext as _
from haystack.query import SearchQuerySet
from pybb.models import Post
from safedelete import HARD_DELETE
from safedelete.queryset import SafeDeleteQueryset
from subscription.models import Subscription

from astrobin.enums import SubjectType
from common.services.constellations_service import ConstellationsService
from common.utils import astrobin_index, get_segregated_reader_database
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty

log = logging.getLogger(__name__)


class UserService:
    user: Optional[User] = None

    def __init__(self, user: Optional[User]):
        self.user = user

    @staticmethod
    def get_case_insensitive(username):
        case_insensitive_matches = User.objects \
            .select_related('userprofile') \
            .prefetch_related('groups') \
            .filter(username__iexact=username)

        count = case_insensitive_matches.count()

        if count == 0:
            raise User.DoesNotExist

        if count == 1:
            return case_insensitive_matches.first()

        return User.objects \
            .select_related('userprofile') \
            .prefetch_related('groups') \
            .get(username__exact=username)

    @staticmethod
    def get_users_in_group_sample(group_name, percent, exclude=None):
        # type: (str, int, User) -> list[User]
        try:
            users = User.objects.filter(groups=Group.objects.get(name=group_name))
            if exclude:
                users = users.exclude(pk=exclude.pk)

            return np.random.choice(list(users), int(math.ceil(users.count() / 100.0 * percent)), replace=False)
        except Group.DoesNotExist:
            return []

    def get_all_images(self, use_union=False) -> QuerySet:
        from astrobin.models import Image
        from common.services.caching_service import CachingService

        cache_key = f"collaborators_check_{self.user.id}"

        has_collaborators = CachingService.get_from_request_cache(cache_key)

        if has_collaborators is None:
            has_collaborators = Image.collaborators.through.objects.filter(user=self.user).exists()
            CachingService.set_in_request_cache(cache_key, has_collaborators)

        if has_collaborators:
            if use_union:
                base_query = Image.objects_including_wip.all()
                query1 = base_query.filter(user=self.user).order_by()
                query2 = base_query.filter(collaborators=self.user).order_by()
                return query1.union(query2).order_by('-published')
            return Image.objects_including_wip.filter(Q(user=self.user) | Q(collaborators=self.user)).distinct()

        return Image.objects_including_wip.filter(user=self.user)

    def get_public_images(self, use_union=True) -> QuerySet:
        from astrobin.models import Image
        from common.services.caching_service import CachingService

        cache_key = f"collaborators_check_{self.user.id}"

        has_collaborators = CachingService.get_from_request_cache(cache_key)

        if has_collaborators is None:
            has_collaborators = Image.collaborators.through.objects.filter(user=self.user).exists()
            CachingService.set_in_request_cache(cache_key, has_collaborators)

        if has_collaborators:
            if use_union:
                base_query = Image.objects.all()
                query1 = base_query.filter(user=self.user).order_by()
                query2 = base_query.filter(collaborators=self.user).order_by()
                return query1.union(query2).order_by('-published')
            return Image.objects.filter(Q(user=self.user) | Q(collaborators=self.user)).distinct()

        return Image.objects.filter(user=self.user)

    def get_wip_images(self, use_union=True) -> QuerySet:
        from astrobin.models import Image
        from common.services.caching_service import CachingService

        cache_key = f"collaborators_check_{self.user.id}"

        has_collaborators = CachingService.get_from_request_cache(cache_key)

        if has_collaborators is None:
            has_collaborators = Image.collaborators.through.objects.filter(user=self.user).exists()
            CachingService.set_in_request_cache(cache_key, has_collaborators)

        if has_collaborators:
            if use_union:
                base_query = Image.wip.all()
                query1 = base_query.filter(user=self.user).order_by()
                query2 = base_query.filter(collaborators=self.user).order_by()
                return query1.union(query2).order_by('-published')
            return Image.wip.filter(Q(user=self.user) | Q(collaborators=self.user)).distinct()

        return Image.wip.filter(user=self.user)

    def get_deleted_images(self) -> QuerySet:
        from astrobin.models import Image
        return Image.deleted_objects.filter(user=self.user)

    def get_bookmarked_images(self) -> QuerySet:
        from astrobin.models import Image

        image_ct: ContentType = ContentType.objects.get_for_model(Image)

        return Image.objects_plain.filter(
            toggleproperties__property_type='bookmark',
            toggleproperties__user=self.user,
            toggleproperties__content_type=image_ct
        )

    def get_liked_images(self) -> QuerySet:
        from astrobin.models import Image

        image_ct: ContentType = ContentType.objects.get_for_model(Image)

        return Image.objects_plain.filter(
            toggleproperties__property_type='like',
            toggleproperties__user=self.user,
            toggleproperties__content_type=image_ct
        )

    def get_image_numbers(self):
        public = self.get_public_images()
        wip = self.get_wip_images()

        return {
            'public_images_no': public.count(),
            'wip_images_no': wip.count(),
            'deleted_images_no': self.get_deleted_images().count(),
        }

    def get_profile_stats(self, request_language: str):
        if not self.user:
            return {}

        user = self.user
        key = f'User.{self.user.pk}.Stats.{request_language}'
        data = cache.get(key)
        if not data:
            user_sqs = SearchQuerySet().models(User).filter(django_id=self.user.pk)
            data = {}

            if user_sqs.count() > 0:
                try:
                    result = user_sqs[0]
                except IndexError:
                    data = {}

                try:
                    data['stats'] = (
                        (_('Member since'), user.date_joined \
                            if user.userprofile.display_member_since \
                            else None, 'datetime'),
                        (_('Last seen online'), user.userprofile.last_seen or user.last_login \
                            if user.userprofile.display_last_seen \
                            else None, 'datetime'),
                        (_('Total integration time'),
                         "%.1f %s" % (result.integration, _("hours")) if result.integration else None),
                        (_('Average integration time'),
                         "%.1f %s" % (result.avg_integration, _("hours")) if user_sqs[
                             0].avg_integration else None),
                        (_('Forum posts written'), "%d" % result.forum_posts if result.forum_posts else 0),
                        (_('Comments written'),
                         "%d" % result.comments_written if result.comments_written else 0),
                        (_('Comments received'), "%d" % result.comments if result.comments else 0),
                        (_('Likes received'),
                         "%d" % result.total_likes_received if result.total_likes_received else 0),
                        (_('Views received'), "%d" % result.views if result.views else 0),
                    )
                except Exception as e:
                    log.error("User page (%d): unable to get stats from search index: %s" % (user.pk, str(e)))
                else:
                    cache.set(key, data, 300)
            else:
                data = {}

        return data

    def shadow_bans(self, other):
        # type: (User) -> bool

        if not hasattr(self.user, 'userprofile') or not hasattr(other, 'userprofile'):
            return False

        return other.userprofile in self.user.userprofile.shadow_bans.all()

    def _real_can_like(self, obj):
        if self.user.is_superuser:
            return True, None

        if not self.user.is_authenticated:
            return False, "ANONYMOUS"

        from common.services.caching_service import CachingService
        cache_key = f'UserService._real_can_like.{self.user.pk}.{obj.__class__.__name__}.{obj.pk}'
        cached = CachingService.get_from_request_cache(cache_key)
        if cached is not None:
            return cached

        if obj.__class__.__name__ == 'Image':
            value = self.user != obj.user, "OWNER"
        elif obj.__class__.__name__ == 'NestedComment':
            value = self.user != obj.author, "OWNER"
        elif obj.__class__.__name__ == 'Post':
            if self.user == obj.user:
                value = False, "OWNER"
            elif obj.topic.closed:
                value = False, "TOPIC_CLOSED"
            else:
                value = True, None
        else:
            value = False, "UNKNOWN"

        CachingService.set_in_request_cache(cache_key, value)
        return value

    def can_like(self, obj):
        return self._real_can_like(obj)[0]

    def can_like_reason(self, obj):
        return self._real_can_like(obj)[1]

    def _real_can_unlike(self, obj):
        if not self.user.is_authenticated:
            return False, "ANONYMOUS"

        from common.services.caching_service import CachingService
        cache_key = f'UserService._real_can_unlike.{self.user.pk}.{obj.__class__.__name__}.{obj.pk}'
        cached = CachingService.get_from_request_cache(cache_key)
        if cached is not None:
            return cached

        toggle_properties = ToggleProperty.objects.toggleproperties_for_object('like', obj, self.user)
        if toggle_properties.exists():
            one_hour_ago = timezone.now() - timedelta(hours=1)
            if toggle_properties.first().created_on > one_hour_ago:
                value = True, None
            else:
                value = False, "TOO_LATE"
        else:
            value = False, "NEVER_LIKED"

        CachingService.set_in_request_cache(cache_key, value)
        return value

    def can_unlike(self, obj):
        return self._real_can_unlike(obj)[0]

    def can_unlike_reason(self, obj):
        return self._real_can_unlike(obj)[1]

    def get_all_comments(self):
        return NestedComment.objects.filter(author=self.user, deleted=False)

    def get_all_forum_posts(self):
        return Post.objects.filter(user=self.user)

    def received_likes_count(self):
        likes = 0

        for image in self.get_all_images().iterator():
            likes += image.like_count

        for comment in self.get_all_comments().iterator():
            likes += len(comment.likes)

        for post in self.get_all_forum_posts().iterator():
            likes += ToggleProperty.objects.filter(
                object_id=post.pk,
                content_type=ContentType.objects.get_for_model(Post),
                property_type='like'
            ).count()

        return likes

    def clear_gallery_image_list_cache(self):
        sections = ('public',)
        subsections = ('title', 'uploaded',)
        views = ('default', 'table',)
        languages = settings.LANGUAGES

        def _do_clear(language_to_clear, section_to_clear, subsection_to_clear, view_to_clear):
            key = make_template_fragment_key(
                'user_gallery_image_list2',
                [self.user.pk, language_to_clear, section_to_clear, subsection_to_clear, view_to_clear]
            )
            cache.delete(key)

        for language in languages:
            for section in sections:
                for subsection in subsections:
                    for view in views:
                        _do_clear(language[0], section, subsection, view)

    def empty_trash(self) -> int:
        from astrobin.models import Image

        images: SafeDeleteQueryset = Image.deleted_objects.filter(user=self.user)
        count: int = images.count()

        images.delete(force_policy=HARD_DELETE)

        return count

    def display_wip_images_on_public_gallery(self) -> bool:
        return self.user.userprofile.display_wip_images_on_public_gallery in (None, True)

    def sort_gallery_by(self, queryset: QuerySet, subsection: str, active: Optional[str]):
        from astrobin.models import Acquisition, Camera, Image, Telescope
        from astrobin_apps_equipment.models import Camera as CameraV2, Telescope as TelescopeV2

        menu = []

        #########
        # TITLE #
        #########
        if subsection == 'title':
            queryset = queryset.order_by('title')

        ############
        # UPLOADED #
        ############
        if subsection == 'uploaded':
            queryset = queryset.order_by('-published', '-uploaded')

        ############
        # ACQUIRED #
        ############
        elif subsection == 'acquired':
            latest_acquisition_date_subquery = Acquisition.objects.filter(
                image_id=OuterRef('pk'),
                date__isnull=False
            ).order_by('-date').values('date')[:1]

            # Apply the subquery to the queryset
            queryset = queryset.filter(
                acquisition__isnull=False
            ).annotate(
                last_acquisition_date=Subquery(latest_acquisition_date_subquery)
            ).order_by(
                '-last_acquisition_date', '-published'
            ).distinct()

        ########
        # YEAR #
        ########
        elif subsection == 'year':
            no_data_message = _("No date specified")
            acquisitions = Acquisition.objects.filter(
                image__user=self.user,
                image__is_wip=False,
                image__deleted=None
            )
            if acquisitions:
                distinct_years = sorted(list(set([a.date.year for a in acquisitions if a.date])), reverse=True)
                menu = [(str(year), str(year)) for year in distinct_years] + [('0', no_data_message)]

                if active == '0':
                    queryset = queryset.filter(
                        Q(
                            subject_type__in=(
                                SubjectType.DEEP_SKY,
                                SubjectType.SOLAR_SYSTEM,
                                SubjectType.WIDE_FIELD,
                                SubjectType.STAR_TRAILS,
                                SubjectType.NORTHERN_LIGHTS,
                                SubjectType.NOCTILUCENT_CLOUDS,
                                SubjectType.LANDSCAPE,
                                SubjectType.ARTIFICIAL_SATELLITE,
                                SubjectType.OTHER
                            )
                        ) &
                        Q(acquisition=None) | Q(acquisition__date=None)
                    ).distinct()
                else:
                    if active in (None, '') and distinct_years:
                        active = str(distinct_years[0])

                    if active:
                        queryset = queryset.filter(acquisition__date__year=active).order_by('-published').distinct()
            else:
                menu = [('0', no_data_message)]
                if active not in (None, ''):
                    active = None
                    queryset = queryset.none()
                else:
                    active = '0'

        ########
        # GEAR #
        ########
        elif subsection == 'gear':
            telescopes = Telescope.objects.filter(
                images_using_for_imaging__user=self.user,
                images_using_for_imaging__deleted__isnull=True,
                images_using_for_imaging__is_wip=False,
            ).distinct()
            cameras = Camera.objects.filter(
                images_using_for_imaging__user=self.user,
                images_using_for_imaging__deleted__isnull=True,
                images_using_for_imaging__is_wip=False,
            ).distinct()

            telescopes_2 = TelescopeV2.objects.filter(
                images_using_for_imaging__user=self.user,
                images_using_for_imaging__deleted__isnull=True,
                images_using_for_imaging__is_wip=False,
            ).distinct()
            cameras_2 = CameraV2.objects.filter(
                images_using_for_imaging__user=self.user,
                images_using_for_imaging__deleted__isnull=True,
                images_using_for_imaging__is_wip=False,
            ).distinct()

            no_data_message = _("No imaging telescopes or lenses, or no imaging cameras specified")
            gear_images_message = _("Gear images")

            # L = LEGACY, N = NEW
            menu += [(f'LT{x.id}', str(x)) for x in telescopes]
            menu += [(f'NT{x.id}', str(x)) for x in telescopes_2]
            menu += [(f'LC{x.id}', str(x)) for x in cameras]
            menu += [(f'NC{x.id}', str(x)) for x in cameras_2]
            menu += [(0, no_data_message)]
            menu += [(-1, gear_images_message)]

            if active == '0':
                queryset = queryset.filter(
                    (
                            Q(subject_type=SubjectType.DEEP_SKY) |
                            Q(subject_type=SubjectType.SOLAR_SYSTEM) |
                            Q(subject_type=SubjectType.WIDE_FIELD) |
                            Q(subject_type=SubjectType.NORTHERN_LIGHTS) |
                            Q(subject_type=SubjectType.NOCTILUCENT_CLOUDS) |
                            Q(subject_type=SubjectType.LANDSCAPE) |
                            Q(subject_type=SubjectType.ARTIFICIAL_SATELLITE) |
                            Q(subject_type=SubjectType.STAR_TRAILS)
                    ) &
                    (Q(imaging_telescopes=None) | Q(imaging_cameras=None))
                ).distinct()
            elif active == '-1':
                queryset = queryset.filter(Q(subject_type=SubjectType.GEAR)).distinct()
            else:
                if active in (None, ''):
                    if telescopes:
                        active = f'LT{telescopes[0].id}'
                    elif telescopes_2:
                        active = f'NT{telescopes_2[0].id}'
                    elif cameras:
                        active = f'LC{cameras[0].id}'
                    elif cameras_2:
                        active = f'NC{cameras_2[0].id}'

                if active:
                    if active.startswith('L'):
                        active_id = active[2:]
                        if not active_id.isdigit():
                            queryset = queryset.none()
                        else:
                            queryset = queryset.filter(
                                Q(imaging_telescopes__id=active_id) |
                                Q(imaging_cameras__id=active_id)
                            ).distinct()
                    elif active.startswith('N'):
                        klass = active[1]
                        active_id = active[2:]
                        if not active_id.isdigit():
                            queryset = queryset.none()
                        else:
                            if klass in (None, 'T', 'telescope'):
                                queryset = queryset.filter(imaging_telescopes_2__id=active_id).distinct()
                            elif klass in ('C', 'camera'):
                                queryset = queryset.filter(imaging_cameras_2__id=active_id).distinct()
                            else:
                                queryset = queryset.none()


        ###########
        # SUBJECT #
        ###########
        elif subsection == 'subject':
            menu += [('DEEP', _("Deep sky"))]
            menu += [('SOLAR', _("Solar system"))]
            menu += [('WIDE', _("Extremely wide field"))]
            menu += [('TRAILS', _("Star trails"))]
            menu += [('NORTHERN_LIGHTS', _("Northern lights"))]
            menu += [('NOCTILUCENT_CLOUDS', _("Noctilucent clouds"))]
            menu += [('LANDSCAPE', _("Landscape"))]
            menu += [('ARTIFICIAL_SATELLITE', _("Artificial satellite"))]
            menu += [('GEAR', _("Gear"))]
            menu += [('OTHER', _("Other"))]

            if active in (None, ''):
                active = 'DEEP'

            if active == 'DEEP':
                queryset = queryset.filter(subject_type=SubjectType.DEEP_SKY)

            elif active == 'SOLAR':
                queryset = queryset.filter(subject_type=SubjectType.SOLAR_SYSTEM)

            elif active == 'WIDE':
                queryset = queryset.filter(subject_type=SubjectType.WIDE_FIELD)

            elif active == 'TRAILS':
                queryset = queryset.filter(subject_type=SubjectType.STAR_TRAILS)

            elif active == 'NORTHERN_LIGHTS':
                queryset = queryset.filter(subject_type=SubjectType.NORTHERN_LIGHTS)

            elif active == 'NOCTILUCENT_CLOUDS':
                queryset = queryset.filter(subject_type=SubjectType.NOCTILUCENT_CLOUDS)

            elif active == 'LANDSCAPE':
                queryset = queryset.filter(subject_type=SubjectType.LANDSCAPE)

            elif active == 'ARTIFICIAL_SATELLITE':
                queryset = queryset.filter(subject_type=SubjectType.ARTIFICIAL_SATELLITE)

            elif active == 'GEAR':
                queryset = queryset.filter(subject_type=SubjectType.GEAR)

            elif active == 'OTHER':
                queryset = queryset.filter(subject_type=SubjectType.OTHER)

        #################
        # CONSTELLATION #
        #################
        elif subsection == 'constellation':
            queryset = queryset.filter(
                Q(subject_type=SubjectType.DEEP_SKY) |
                Q(subject_type=SubjectType.WIDE_FIELD)
            )

            unique_constellations = queryset.filter(
                constellation__isnull=False
            ).values_list(
                'constellation', flat=True
            ).distinct()

            menu += [('ALL', _('All'))]
            for constellation in ConstellationsService.constellation_table:
                if constellation[0] in unique_constellations:
                    menu += [(constellation[0], constellation[1])]

            if queryset.filter(constellation__isnull=True).exists():
                menu += [('n/a', _('n/a'))]

            if active in (None, ''):
                active = 'ALL'

            if active != 'ALL':
                try:
                    queryset = queryset.filter(constellation=active)
                except KeyError:
                    log.warning("Requested missing constellation %s for user %d" % (active, self.user.pk))
                    queryset = Image.objects.none()

        ###########
        # NO DATA #
        ###########
        elif subsection == 'nodata':
            menu += [('GEAR', _("No imaging telescopes or lenses, or no imaging cameras specified"))]
            menu += [('ACQ', _("No acquisition details specified"))]

            if active is None:
                active = 'GEAR'

            if active == 'GEAR':
                queryset = queryset.filter(
                    Q(
                        subject_type__in=(
                            SubjectType.DEEP_SKY,
                            SubjectType.SOLAR_SYSTEM,
                            SubjectType.WIDE_FIELD,
                            SubjectType.STAR_TRAILS,
                            SubjectType.NORTHERN_LIGHTS,
                            SubjectType.NOCTILUCENT_CLOUDS,
                            SubjectType.LANDSCAPE,
                            SubjectType.ARTIFICIAL_SATELLITE,
                        )
                    ) &
                    (
                            Q(Q(imaging_telescopes=None) | Q(imaging_cameras=None)) &
                            Q(Q(imaging_telescopes_2=None) | Q(imaging_cameras_2=None))
                    )
                ).distinct()

            elif active == 'ACQ':
                queryset = queryset.filter(
                    Q(
                        subject_type__in=(
                            SubjectType.DEEP_SKY,
                            SubjectType.SOLAR_SYSTEM,
                            SubjectType.WIDE_FIELD,
                            SubjectType.STAR_TRAILS,
                            SubjectType.NORTHERN_LIGHTS,
                            SubjectType.NOCTILUCENT_CLOUDS,
                            SubjectType.LANDSCAPE,
                            SubjectType.ARTIFICIAL_SATELLITE,
                        )
                    ) &
                    Q(acquisition=None)
                )

        return queryset, menu, active

    def update_premium_counter_on_subscription(self, subscription: Subscription):
        from astrobin.models import Image, UserProfile

        profile: UserProfile = self.user.userprofile

        if subscription.group.name == 'astrobin_lite':
            profile.premium_counter = 0
            profile.save(keep_deleted=True)
        elif subscription.group.name == 'astrobin_lite_2020':
            profile.premium_counter = Image.objects_including_wip.filter(user=self.user).count()
            profile.save(keep_deleted=True)

    def start_platesolving_tasks(self):
        from astrobin_apps_platesolving.tasks import start_basic_solver

        for image in self.get_all_images():
            start_basic_solver.delay(image.pk, ContentType.objects.get_for_model(image).pk)
            for revision in image.revisions.all():
                start_basic_solver.delay(revision.pk, ContentType.objects.get_for_model(revision).pk)

    def is_in_group(self, group_name: Union[str, List[str]]) -> bool:
        if not self.user or not self.user.is_authenticated:
            return False

        from common.services.caching_service import CachingService

        cache_key = f'all_groups_{self.user.pk}'
        all_groups = CachingService.get(cache_key)
        if all_groups is None:
            all_groups = list(self.user.groups.values_list('name', flat=True))
            CachingService.set(cache_key, all_groups, 300)

        if type(group_name) is list:
            return any([x in all_groups for x in group_name])

        return group_name in all_groups

    def is_in_astrobin_group(self, group_name: Union[str, List[str]]) -> bool:
        if not self.user or not self.user.is_authenticated:
            return False

        if type(group_name) is list:
            return (
                    self.user.joined_group_set.filter(name__in=group_name).exists() or
                    self.user.owned_group_set.filter(name__in=group_name).exists()
            )

        return (
            self.user.joined_group_set.filter(name=group_name).exists() or
            self.user.owned_group_set.filter(name=group_name).exists()
        )

    def set_last_seen(self, country_code: str):
        from astrobin.models import UserProfile

        try:
            profile: UserProfile = UserProfile.objects.get(user=self.user)
            profile.last_seen = datetime.now()

            if country_code and country_code != 'UNKNOWN':
                try:
                    profile.last_seen_in_country = country_code.lower()[0:2]
                except IndexError:
                    profile.last_seen_in_country = None
            else:
                profile.last_seen_in_country = None

            profile.save(keep_deleted=True)
        except UserProfile.DoesNotExist:
            pass

    def set_signup_country(self, country_code: str):
        from astrobin.models import UserProfile

        try:
            profile: UserProfile = UserProfile.objects.get(user=self.user)

            if country_code and country_code != 'UNKNOWN':
                try:
                    profile.signup_country = country_code.lower()[0:2]
                except IndexError:
                    profile.signup_country = None
            else:
                profile.signup_country = None

            profile.save(keep_deleted=True)
        except UserProfile.DoesNotExist:
            pass

    def has_used_commercial_remote_hosting_facilities(self):
        from astrobin.models import Image

        cache_key = f'UserService.has_used_commercial_remote_hosting_facilities.{self.user.pk}'

        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        value = Image.objects_including_wip.filter(
            Q(user=self.user) & Q(remote_source__isnull=False) & ~Q(remote_source='OWN')
        ).exists()
        cache.set(cache_key, value, 60 * 60 * 24)

        return value

    def agreed_to_iotd_tp_rules_and_guidelines(self) -> bool:
        agreed = self.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines
        return agreed and agreed > settings.IOTD_LAST_RULES_UPDATE

    def compute_contribution_index(self) -> float:
        def compute_comment_contribution_index(comments: QuerySet):
            min_comment_length = 150
            min_likes = 3

            all_comments = comments \
                .annotate(length=Length('text')) \
                .filter(deleted=False, length__gte=min_comment_length)

            all_comments_with_enough_likes = [x for x in all_comments if len(x.likes) >= min_likes]
            all_comments_count = len(all_comments_with_enough_likes)

            if all_comments_count == 0:
                return 0

            all_likes = 0
            for comment in all_comments_with_enough_likes:
                all_likes += len(comment.likes)

            average = all_likes / float(all_comments_count)
            normalized = []

            for comment in all_comments_with_enough_likes:
                likes = len(comment.likes)
                if likes >= average:
                    normalized.append(likes)

            if len(normalized) == 0:
                return 0

            return astrobin_index(normalized)

        def compute_forum_post_contribution_index(posts: QuerySet):
            min_post_length = 150
            min_likes = 3

            all_posts = posts \
                .annotate(length=Length('body')) \
                .filter(length__gte=min_post_length)

            all_posts_with_enough_likes = [
                x \
                for x in all_posts \
                if ToggleProperty.objects.toggleproperties_for_object('like', x).count() >= min_likes
            ]
            all_posts_count = len(all_posts_with_enough_likes)

            if all_posts_count == 0:
                return 0

            all_likes = 0
            for post in all_posts_with_enough_likes:
                all_likes += ToggleProperty.objects.toggleproperties_for_object('like', post).count()

            average = all_likes / float(all_posts_count)
            normalized = []

            for post in all_posts_with_enough_likes:
                likes = ToggleProperty.objects.toggleproperties_for_object('like', post).count()
                if likes >= average:
                    normalized.append(likes)

            if len(normalized) == 0:
                return 0

            return astrobin_index(normalized)

        comments_contribution_index = compute_comment_contribution_index(
            NestedComment.objects.using(get_segregated_reader_database()).filter(author=self.user)
        )

        forum_post_contribution_index = compute_forum_post_contribution_index(
            Post.objects.using(get_segregated_reader_database()).filter(user=self.user)
        )

        total = comments_contribution_index + forum_post_contribution_index

        log.debug(
            f"User {self.user.username} has a contribution index of {total} (comments: "
            f"{comments_contribution_index}, forum posts: {forum_post_contribution_index})"
        )

        return total

    def compute_image_index(self) -> float:
        public_images = UserService(self.user).get_public_images(use_union=False)

        likes = public_images.aggregate(total_likes=Sum('like_count'))['total_likes']
        images = self.user.userprofile.image_count
        average = likes / images if images > 0 else 0

        # Only consider images that have a number of likes greater than the average.
        normalized = list(
            public_images.filter(like_count__gte=average).values_list('like_count', flat=True)
        )

        if len(normalized) == 0:
            result = 0
        else:
            result = astrobin_index(normalized)

        if self.user.userprofile.astrobin_index_bonus is not None:
            result += self.user.userprofile.astrobin_index_bonus

        log.debug(f"User {self.user.username} has an image index of {result}")

        return result

    def update_followers_count(self):
        from astrobin.models import UserProfile

        try:
            profile: UserProfile = self.user.userprofile
        except:
            return

        if profile:
            profile.followers_count = ToggleProperty.objects.filter(
                property_type='follow',
                object_id=self.user.pk,
                content_type=ContentType.objects.get_for_model(User)
            ).count()
            profile.save(keep_deleted=True)

    def update_following_count(self):
        from astrobin.models import UserProfile

        try:
            profile: UserProfile = self.user.userprofile
        except:
            return

        if profile:
            profile.following_count = ToggleProperty.objects.filter(
                user=self.user,
                property_type='follow',
                content_type=ContentType.objects.get_for_model(User)
            ).count()
            profile.save(keep_deleted=True)

    def update_image_count(self):
        from astrobin.models import UserProfile

        try:
            profile: UserProfile = self.user.userprofile
        except:
            return

        if profile:
            profile.image_count = UserService(self.user).get_public_images().count()
            profile.wip_image_count = UserService(self.user).get_wip_images().count()
            profile.deleted_image_count = UserService(self.user).get_deleted_images().count()
            profile.save(keep_deleted=True)
