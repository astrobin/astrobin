from django import forms
from django.utils.translation import gettext, ugettext as _

from astrobin.forms.utils import NULL_CHOICE
from astrobin.models import Collection
from astrobin_apps_images.models import KeyValueTag


class CollectionUpdateForm(forms.ModelForm):
    error_css_class = 'error'

    order_by_tag = forms.ChoiceField(
        required=False,
        help_text=_("Select a tag to order this collection by its value. If you see no options here, it's because "
                    "none of the images in this collection have key/value tags. PS: Images that lack this tag will "
                    "appear at the bottom of the collection.")
    )

    def __init__(self, *args, **kwargs):
        super(CollectionUpdateForm, self).__init__(*args, **kwargs)

        tag_keys = KeyValueTag.objects \
            .filter(image__user=self.instance.user) \
            .distinct() \
            .values_list("key", flat=True)

        self.fields['cover'].required = False
        self.fields['cover'].widget.attrs.update(
            {
                'data-allow-clear': 'true',
                'data-placeholder': gettext('Use the most recent image automatically')
            }
        )

        self.fields['order_by_tag'].choices = NULL_CHOICE + [(x, x) for x in tag_keys]
        self.fields['order_by_tag'].widget.attrs.update(
            {
                'data-allow-clear': 'true',
                'data-placeholder': '--------'
            }
        )

        self.fields['parent'].queryset = Collection.objects.filter(
            user=self.instance.user
        ).exclude(
            pk=self.instance.pk
        ).order_by(
            'name'
        )
        self.fields['parent'].widget.attrs.update(
            {
                'data-allow-clear': 'true',
                'data-placeholder': '--------'
            }
        )

    class Meta:
        model = Collection
        fields = ('name', 'description', 'parent', 'cover', 'order_by_tag')
