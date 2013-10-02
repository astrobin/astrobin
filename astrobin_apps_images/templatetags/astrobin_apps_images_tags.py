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


# Renders an linked image tag with a placeholder and async loading of the
# actual thumbnail.
def astrobin_image(
    context, image, alias,
    revision = 'final', url_size = 'regular'):

    size  = settings.THUMBNAIL_ALIASES[''][alias]['size']
    if alias in ('regular', 'regular_inverted',
                 'hd'     , 'hd_inverted',
                 'real'   , 'real_inverted'):
        size = (size[0], int(size[0] / (image.w / float(image.h))))

    url = get_image_url(image, revision, url_size)
    show_tooltip = alias in (
        'gallery', 'gallery_inverted',
        'thumb', 'runnerup',
    )

    return {
        'image'       : image,
        'alias'       : alias,
        'revision'    : revision,
        'size'        : "%sx%s" % (size[0], size[1]),
        'url'         : url,
        'show_tooltip': show_tooltip,
        'request'     : context['request'],
    }


register.inclusion_tag(
    'astrobin_apps_images/snippets/image.html',
    takes_context = True)(astrobin_image)
