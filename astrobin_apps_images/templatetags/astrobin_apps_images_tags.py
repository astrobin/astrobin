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
def get_image_url(image):
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

    return image.get_absolute_url()


# Renders an linked image tag with a placeholder and async loading of the
# actual thumbnail.
@register.simple_tag
def astrobin_image(image, alias, revision = 'final'):
    size  = settings.THUMBNAIL_ALIASES[''][alias]['size']

    return render_to_string(
        'astrobin_apps_images/snippets/image.html',
        {
            'image'   : image,
            'alias'   : alias,
            'revision': revision,
            'size'    : "%sx%s" % (size[0], size[1]),
        },
        None)

