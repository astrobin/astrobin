import logging
import random
import string
import zlib
from datetime import datetime, timedelta

from PIL.Image import DecompressionBombError
from annoying.functions import get_object_or_None
from django.conf import settings
from django.core.cache import cache
from django.template import Library
from django.urls import reverse
from django.utils.translation import ugettext as _

from astrobin.models import Collection, Image, ImageRevision
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import IotdSubmission, IotdVote
from astrobin_apps_iotd.services import IotdService
from common.services import AppRedirectionService

register = Library()
logger = logging.getLogger(__name__)


# Returns the URL of an image, taking into account the fact that it might be
# a commercial gear image.
@register.simple_tag
def get_image_url(image, revision='final', size='regular'):
    return image.get_absolute_url(revision, size)


@register.filter
def gallery_thumbnail(image, revision_label):
    return image.thumbnail('gallery', revision_label)


@register.filter
def gallery_thumbnail_inverted(image, revision_label):
    return image.thumbnail('gallery_inverted', revision_label)


# Renders an linked image tag with a placeholder and async loading of the
# actual thumbnail.
def astrobin_image(context, image, alias, **kwargs):
    request = kwargs.get('request', context['request'])

    revision_label = kwargs.get('revision', 'final')
    url_size = kwargs.get('url_size', 'regular')
    url_revision = kwargs.get('url_revision', revision_label)
    link = kwargs.get('link', True)
    link_alias = kwargs.get('link_alias', alias)
    tooltip = kwargs.get('tooltip', True)
    nav_ctx = kwargs.get('nav_ctx', request.GET.get('nc', context.get('nav_ctx')))
    nav_ctx_extra = kwargs.get('nav_ctx_extra', request.GET.get('nce', context.get('nav_ctx_extra')))
    classes = kwargs.get('classes', '')
    instant = kwargs.get('instant', False)
    fancybox = kwargs.get('fancybox', False)
    fancybox_tooltip = kwargs.get('fancybox_tooltip', False)
    rel = kwargs.get('rel', '')
    slug = kwargs.get('slug', '')

    if nav_ctx == 'user':
        # None is considered to be default for 'user'
        nav_ctx = None

    response_dict = {
        'provide_size': True,
    }

    if alias in (None, ''):
        alias = 'gallery'

    mod = 'inverted' if 'inverted' in link_alias else None
    size = settings.THUMBNAIL_ALIASES[''][alias]['size']

    if image is None or not isinstance(image, Image):
        return {
            'status': 'failure',
            'image': '',
            'alias': alias,
            'revision': revision_label,
            'revision_title': None,
            'size_x': size[0],
            'size_y': size[1],
            'caption_cache_key': 'astrobin_image_no_image',
            'nav_ctx': nav_ctx,
            'nav_ctx_extra': nav_ctx_extra,
            'classes': classes,
            'is_revision': False,
            'instant': False,
            'fancybox': False,
            'fancybox_tooltip': False,
            'fancybox_url': None,
            'rel': rel,
            'slug': slug,
            'show_video': False,
            'show_play_icon': False,
        }

    # Old images might not have a size in the database, let's fix it.
    image_revision = image
    if revision_label == 'final':
        revision_label = ImageService(image).get_final_revision_label()
    if revision_label not in [0, '0']:
        try:
            image_revision = image.revisions.get(label=revision_label)
        except ImageRevision.DoesNotExist:
            # Image revision was deleted
            pass

    w = image_revision.w
    h = image_revision.h

    if w == 0 or h == 0 or w is None or h is None:
        try:
            from django.core.files.images import get_image_dimensions
            (w, h) = get_image_dimensions(image_revision.image_file.file)
            if w and h:
                image_revision.w = w
                image_revision.h = h
                image_revision.save(keep_deleted=True)
            else:
                logger.warning("astrobin_image tag: unable to get image dimensions for revision %d" % image_revision.pk)
                response_dict['status'] = 'error'
                response_dict['error_message'] = _("Data corruption. Please upload this image again. Sorry!")
        except (IOError, ValueError, DecompressionBombError) as e:
            w = size[0]
            h = size[1] if size[1] > 0 else w
            logger.warning(
                "astrobin_image tag: unable to get image dimensions for revision %d: %s" % (
                    image_revision.pk, str(e))
                )
            response_dict['status'] = 'error'
            response_dict['error_message'] = _("Data corruption. Please upload this image again. Sorry!")
        except (TypeError, zlib.error) as e:
            w = size[0]
            h = size[1] if size[1] > 0 else w
            logger.warning(
                "astrobin_image tag: unable to get image dimensions for revision %d: %s" % (
                    image_revision.pk, str(e))
                )

    if ImageService.is_viewable_alias(alias) and w is not None and h is not None:
        size = (size[0], int(size[0] / (w / float(h))))
        response_dict['provide_size'] = False

    placehold_size = [size[0], size[1]]
    for i in range(0, 2):
        if placehold_size[i] > 1920:
            placehold_size[i] = 1920

    if w is not None and w < placehold_size[0]:
        placehold_size[0] = w
        placehold_size[1] = h

    # Determine whether this is an animated gif, and we should show it as such
    field = image.get_thumbnail_field(revision_label)
    if not field.name.startswith('images/'):
        field.name = 'images/' + field.name

    animated = field.name.lower().endswith('.gif') and ImageService.is_viewable_alias(alias)

    url = get_image_url(image, url_revision, url_size)

    show_tooltip = tooltip and ImageService.is_tooltip_compatible_alias(alias)

    ##########
    # BADGES #
    ##########

    badges = []

    if ImageService.is_badge_compatible_alias(alias):
        iotd_service = IotdService()

        if image.is_wip:
            badges.append('wip')

        if image.video_file.name and not ImageService.is_viewable_alias(alias):
            badges.append('video')

        if image.submitted_for_iotd_tp_consideration and not image.disqualified_from_iotd_tp:
            num_submissions = IotdSubmission.objects.filter(image=image).count()
            num_votes = IotdVote.objects.filter(image=image).count()

            if num_submissions < settings.IOTD_SUBMISSION_MIN_PROMOTIONS:
                cutoff = datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS)
            elif num_votes < settings.IOTD_REVIEW_MIN_PROMOTIONS:
                cutoff = datetime.now() - timedelta(
                    settings.IOTD_SUBMISSION_WINDOW_DAYS + settings.IOTD_REVIEW_WINDOW_DAYS
                )
            else:
                cutoff = datetime.now() - timedelta(
                    settings.IOTD_SUBMISSION_WINDOW_DAYS +
                    settings.IOTD_REVIEW_WINDOW_DAYS +
                    settings.IOTD_JUDGEMENT_WINDOW_DAYS
                )

            if iotd_service.is_iotd(image):
                badges.append('iotd')
            elif iotd_service.is_top_pick(image):
                badges.append('top-pick')
            elif iotd_service.is_top_pick_nomination(image):
                badges.append('top-pick-nomination')
            elif (
                    iotd_service.is_future_iotd(image) or
                    image.submitted_for_iotd_tp_consideration > cutoff - timedelta(minutes=30)
            ):
                if hasattr(request, 'user') and (request.user == image.user or request.user.is_superuser):
                    badges.append('iotd-queue')

            if (
                    hasattr(request, 'user') and
                    (image.user == request.user or request.user.is_superuser) and
                    str(image.get_id()) in request.path and
                    bool(set(badges) & {'iotd', 'top-pick', 'top-pick-nomination', 'iotd-queue'})
            ):
                badges.append('iotd-stats')

        if image.collaborators.exists():
            badges.append('collaboration')

        # Temporarily disable this because it hogs the default celery queue.
        """
        cache_key = 'top100_ids'
        top100_ids = cache.get(cache_key)
        if top100_ids is None:
            from astrobin.tasks import update_top100_ids
            update_top100_ids.delay()
        elif image.pk in top100_ids:
            badges.append('top100')
        """

    cache_key = image.thumbnail_cache_key(field, alias, revision_label)
    if animated:
        cache_key += '_animated'
    thumb_url = cache.get(cache_key)

    # Force HTTPS
    if thumb_url and request.is_secure():
        thumb_url = thumb_url.replace('http://', 'https://', 1)

    # If we're testing or this is a video, we want to bypass the placeholder thing and force-get the thumb url.
    if thumb_url is None and (image_revision.video_file.name or settings.TESTING):
        thumb = image.thumbnail_raw(alias, revision_label)
        if thumb:
            thumb_url = thumb.url

    get_thumb_url = None
    get_raw_thumb_url = None
    if thumb_url is None:
        get_thumb_kwargs = {
            'id': image.hash if image.hash else image.id,
            'alias': alias,
        }

        if revision_label is None or revision_label != 'final':
            get_thumb_kwargs['r'] = revision_label

        get_thumb_url = reverse('image_thumb', kwargs=get_thumb_kwargs)
        if animated:
            get_thumb_url += '?animated'

        get_raw_thumb_url = reverse('image_rawthumb', kwargs=get_thumb_kwargs)
        if animated:
            get_raw_thumb_url += '?animated'

    get_regular_large_thumb_url, regular_large_thumb_url = ImageService(image).get_enhanced_thumb_url(
        field, alias, revision_label, animated, request.is_secure(), 'regular_large'
    )

    get_enhanced_thumb_url, enhanced_thumb_url = ImageService(image).get_enhanced_thumb_url(
        field, alias, revision_label, animated, request.is_secure(), 'hd'
    )

    collection_tag_key = None
    collection_tag_value = None
    if (
        hasattr(request, 'user') and
        request.user == image.user and
        hasattr(request, 'resolver_match') and
        hasattr(request.resolver_match, 'kwargs') and
        'collection_pk' in request.resolver_match.kwargs
    ):
        collection = get_object_or_None(Collection, pk=request.resolver_match.kwargs['collection_pk'])
        if collection:
            collection_tag_key = collection.order_by_tag
            collection_tag_value = ImageService(image).get_collection_tag_value(collection)


    # noinspection PyTypeChecker
    return dict(
        list(response_dict.items()) + list(
            {
                'status': 'success',
                'image': image,
                'alias': alias,
                'mod': mod,
                'revision': revision_label,
                'size_x': size[0],
                'size_y': size[1],
                'placehold_size': "%sx%s" % (placehold_size[0], placehold_size[1]),
                'real': alias in ('real', 'real_inverted'),
                'url': url,
                'show_tooltip': show_tooltip,
                'request': request,
                'caption_cache_key': "%d_%s_%s_%s_%d" % (
                    image.id,
                    revision_label,
                    alias,
                    request.LANGUAGE_CODE if hasattr(request, "LANGUAGE_CODE") else "en",
                    request.user == image.user if hasattr(request, "user") else False
                ),
                'collection_tag_key': collection_tag_key,
                'collection_tag_value': collection_tag_value,
                'badges': badges,
                'animated': animated,
                'get_thumb_url': get_thumb_url,
                'get_raw_thumb_url': get_raw_thumb_url,
                'thumb_url': thumb_url,
                'link': link,
                'nav_ctx': nav_ctx,
                'nav_ctx_extra': nav_ctx_extra,
                'classes': classes,
                'enhanced_thumb_url': enhanced_thumb_url,
                'get_enhanced_thumb_url': get_enhanced_thumb_url,
                'regular_large_thumb_url': regular_large_thumb_url,
                'get_regular_large_thumb_url': get_regular_large_thumb_url,
                'image_revision': image_revision,
                'is_revision': hasattr(image_revision, 'label'),
                'revision_id': image_revision.pk,
                'revision_title': image_revision.title if hasattr(image_revision, 'label') else None,
                'w': w,
                'h': h,
                'instant': instant,
                'fancybox': fancybox,
                'fancybox_tooltip': fancybox_tooltip,
                'fancybox_url':
                    image_revision.encoded_video_file.url if image_revision.encoded_video_file.name else settings.BASE_URL + reverse(
                        'image_rawthumb', kwargs={
                            'id': image.get_id(),
                            'alias': 'qhd',
                            'r': revision_label,
                        }
                    ) + '?sync' + ('&animated' if field.name.lower().endswith('.gif') else ''),
                'rel': rel,
                'slug': slug,
                'is_video': bool(image_revision.video_file.name),
                'show_video': ImageService.is_viewable_alias(alias) and (
                    bool(image_revision.video_file.name) if hasattr(image_revision, 'label') else bool(
                        image.video_file.name
                    )
                ),
                'show_play_icon': ImageService.is_play_button_alias(alias),
            }.items()
        )
        )


register.inclusion_tag(
    'astrobin_apps_images/snippets/image.html',
    takes_context=True
)(astrobin_image)


@register.simple_tag(takes_context=True)
def random_id(context, size=8, chars=string.ascii_uppercase + string.digits):
    id = ''.join(random.choice(chars) for x in range(size))
    context['randomid'] = id
    return ''


@register.simple_tag(takes_context=True)
def cache_image_list(context):
    # Don't cache for gallery owner.
    if context['requested_user'] and context['request'].user == context['requested_user']:
        return False

    if context['request'].user.is_superuser:
        return False

    # Don't cache pages.
    if context['request'].GET.get('image_list_page'):
        return False

    return context['section'] == 'public' and (context['subsection'] in ('title', 'uploaded',))


@register.filter()
def is_platesolvable(image):
    return ImageService(image).is_platesolvable()


@register.filter()
def needs_premium_subscription_to_platesolve(image):
    return ImageService(image).needs_premium_subscription_to_platesolve()


@register.filter()
def revision_upload_url(image: Image, request):
    return AppRedirectionService.redirect('/uploader/revision/%d' % image.pk)


@register.filter
def display_download_menu(user, image):
    return ImageService(image).display_download_menu(user)
