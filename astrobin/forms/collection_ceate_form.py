from django import forms

from astrobin.forms.utils import NULL_CHOICE
from astrobin.models import Collection
from astrobin_apps_images.models import KeyValueTag


class CollectionCreateForm(forms.ModelForm):
    error_css_class = 'error'

    order_by_tag = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')

        super(CollectionCreateForm, self).__init__(*args, **kwargs)

        tag_keys = KeyValueTag.objects \
            .filter(image__user=user) \
            .distinct() \
            .values_list("key", flat=True)

        self.fields['order_by_tag'].choices = NULL_CHOICE + [(x, x) for x in tag_keys]

    class Meta:
        model = Collection
        fields = ('name', 'description', 'order_by_tag')
