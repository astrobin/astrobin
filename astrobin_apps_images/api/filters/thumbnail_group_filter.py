from django.forms import CheckboxSelectMultiple
from django_filters import FilterSet, ModelMultipleChoiceFilter

from astrobin.models import Image
from astrobin_apps_images.models import ThumbnailGroup


class ThumbnailGroupFilter(FilterSet):
    image = ModelMultipleChoiceFilter(
        queryset=Image.objects_including_wip.all(),
        field_name='image__pk',
        to_field_name="pk",
        widget=CheckboxSelectMultiple(),
        label="Image",
        label_suffix="",
    )

    class Meta:
        model = ThumbnailGroup
        fields = ('image',)
