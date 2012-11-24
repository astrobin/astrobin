# Django
from django.template import Library
from django.utils.translation import ugettext_lazy as _

# This app
from rawdata.models import RawImage

register = Library() 

@register.filter
def humanize_rawimage_type(image_type):
    for choice in RawImage.TYPE_CHOICES:
        if image_type == choice[0]:
            return choice[1]
    return _("Unknown")
