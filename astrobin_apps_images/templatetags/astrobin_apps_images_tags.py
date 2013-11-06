# Python
import random
import string
from PIL import Image as PILImage

# Django
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.template import Library, Node
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

# AstroBin
from astrobin.models import CommercialGear, Gear
from astrobin.models import Image

# Third party
from haystack.query import SearchQuerySet


register = Library()

# Returns the URL of an image, taking into account the fact that it might be
# a commercial gear image.
@register.simple_tag
def get_image_url(image, revision = 'final', size = 'regular'):
    def commercial_gear_url(commercial_gear):
        gear = Gear.objects.filter(commercial = commercial_gear)
        if gear:
            return gear[0].get_absolute_url()
        return None

    try:
        commercial_gear = image.featured_gear.all()[0]
        url = commercial_gear_url(commercial_gear)
        if url:
            return url

    except IndexError:
        pass

    return image.get_absolute_url(revision, size)


@register.filter
def gallery_thumbnail(image, revision_label):
    return image.thumbnail('gallery', {'revision_label': revision_label})


@register.filter
def gallery_thumbnail_inverted(image, revision_label):
    return image.thumbnail('gallery_inverted', {'revision_label': revision_label})


# Renders an linked image tag with a placeholder and async loading of the
# actual thumbnail.
def astrobin_image(
    context, image, alias,
    revision = 'final', url_size = 'regular',
    mod = None):

    response_dict = {
        'provide_size': True,
    }

    if alias == '':
        alias = 'thumb'

    size  = settings.THUMBNAIL_ALIASES[''][alias]['size']

    if image is None or not isinstance(image, Image):
        return {
            'status': 'failure',
            'image': '',
            'alias': alias,
            'revision': revision,
            'mod': mod,
            'size_x': size[0],
            'size_y': size[1],
            'cache_key': 'astrobin_image_no_image',
        }

    w = image.w
    h = image.h

    if w == 0 or h == 0:
        # Old images might not have a size in the database, let's fix it.
        try:
            from django.core.files.images import get_image_dimensions
            (w, h) = get_image_dimensions(image.image_file.file)
            image.w = w
            image.h = h
            image.save()
        except IOError:
            w = size[0]
            h = size[1] if size[1] > 0 else w
            response_dict['status'] = 'error'
            response_dict['error_message'] = _("Data corruption. Please upload this image again. Sorry!")

    if alias in ('regular', 'regular_inverted',
                 'hd'     , 'hd_inverted',
                 'real'   , 'real_inverted'):
        size = (size[0], int(size[0] / (w / float(h))))
        response_dict['provide_size'] = False

    placehold_size = [size[0], size[1]]
    for i in range(0,2):
        if placehold_size[i] > 1920:
            placehold_size[i] = 1920

    if w < placehold_size[0]:
        placehold_size[0] = w
        placehold_size[1] = h

    # Determine whether this is an animated gif, and we should show it as such
    animated = False
    if image.image_file.name.lower().endswith('.gif') and alias in ('regular', 'hd', 'real'):
        gif = PILImage.open(image.image_file.file)
        try:
            gif.seek(1)
        except EOFError:
            animated = False
        else:
            animated = True

    url = get_image_url(image, revision, url_size)

    show_tooltip = alias in (
        'gallery', 'gallery_inverted',
        'thumb', 'runnerup',
    )


    ##########
    # BADGES #
    ##########

    badges = []

    if alias in ('thumb', 'gallery', 'regular'):
        if image.iotd_date():
            badges.append('iotd')

        top100_ids = SearchQuerySet().models(Image).all().order_by('-likes').values_list('django_id', flat = True)[:100]
        if image.pk in top100_ids:
            badges.append('top100')


    cache_key = 'easy_thumb_alias_cache_%s.%s_%s_%s' % (
        'astrobin.image',
        image.get_thumbnail_field(revision),
        alias,
        mod)

    thumb_url = cache.get(cache_key)

    get_thumb_url = None
    if thumb_url is None:
        get_thumb_kwargs = {
            'id': image.id,
            'alias': alias,
        }
        if mod:
            get_thumb_kwargs['mod'] = mod
        if revision is None or revision != 'final':
            get_thumb_kwargs['r'] = revision

        get_thumb_url = reverse('image_thumb', kwargs = get_thumb_kwargs)
        if animated:
            get_thumb_url += '?animated'

    return dict(response_dict.items() + {
        'status'        : 'success',
        'image'         : image,
        'alias'         : alias,
        'revision'      : revision,
        'size_x'        : size[0],
        'size_y'        : size[1],
        'placehold_size': "%sx%s" % (placehold_size[0], placehold_size[1]),
        'mod'           : mod,
        'real'          : alias in ('real', 'real_inverted'),
        'url'           : url,
        'show_tooltip'  : show_tooltip,
        'request'       : context['request'],
        'cache_key'     : "%s_%s_%s_%d" % (mod if mod else 'none', alias, revision, image.id),
        'badges'        : badges,
        'animated'      : animated,
        'get_thumb_url' : get_thumb_url,
        'thumb_url'     : thumb_url,
    }.items())


@register.simple_tag(takes_context = True)
def random_id(context, size = 8, chars = string.ascii_uppercase + string.digits):
    id = ''.join(random.choice(chars) for x in range(size))
    context['randomid'] = id
    return ''


register.inclusion_tag(
    'astrobin_apps_images/snippets/image.html',
    takes_context = True)(astrobin_image)
