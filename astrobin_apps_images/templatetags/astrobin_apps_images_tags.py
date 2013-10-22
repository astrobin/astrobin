# Python
import random
import string

# Django
from django.conf import settings
from django.template import Library, Node
from django.template.loader import render_to_string

# AstroBin
from astrobin.models import CommercialGear, Gear


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
        commercial_gear = CommercialGear.objects.get(image = image)
        url = commercial_gear_url(commercial_gear)
        if url:
            return url

    except CommercialGear.DoesNotExist:
        pass
    except CommercialGear.MultipleObjectsReturned:
        commercial_gear = CommercialGear.objects.filter(image = image)[0]
        url = commercial_gear_url(commercial_gear)
        if url:
            return url

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

    if alias == '':
        alias = 'thumb'

    size  = settings.THUMBNAIL_ALIASES[''][alias]['size']

    w = image.w
    h = image.h

    if w == 0 or h == 0:
        # Old images might not have a size in the database, let's fix it.
        from django.core.files.images import get_image_dimensions
        (w, h) = get_image_dimensions(image.image_file)
        image.w = w
        image.h = h
        image.save()

    if alias in ('regular', 'regular_inverted',
                 'hd'     , 'hd_inverted',
                 'real'   , 'real_inverted'):
        size = (size[0], int(size[0] / (image.w / float(image.h))))

    placehold_size = [size[0], size[1]]
    for i in range(0,2):
        if placehold_size[i] > 1920:
            placehold_size[i] = 1920

    url = get_image_url(image, revision, url_size)
    show_tooltip = alias in (
        'gallery', 'gallery_inverted',
        'thumb', 'runnerup',
    )

    return {
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
        'cache_key'     : "%s_%s_%s_%d" % (mod if mod else 'none', alias, revision, image.id)
    }


@register.simple_tag(takes_context = True)
def random_id(context, size = 8, chars = string.ascii_uppercase + string.digits):
    id = ''.join(random.choice(chars) for x in range(size))
    context['randomid'] = id
    return ''


register.inclusion_tag(
    'astrobin_apps_images/snippets/image.html',
    takes_context = True)(astrobin_image)
