from braces.views import JSONResponseMixin
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views import View

from astrobin.models import Image
from astrobin.utils import get_client_country_code
from astrobin_apps_equipment.models import Accessory, Camera, Filter, Mount, Software, Telescope
from astrobin_apps_images.services import ImageService
from common.constants import GroupName


class EquipmentItemPopover(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        item_type = kwargs.pop('type')
        pk = kwargs.pop('pk')
        image_id = kwargs.pop('image_id')
        klass_map = {
            'telescope': Telescope,
            'camera': Camera,
            'mount': Mount,
            'filter': Filter,
            'software': Software,
            'accessory': Accessory,
        }

        klass = klass_map.get(item_type.lower(), None)
        if klass is None:
            raise Http404

        image = ImageService.get_object(image_id, Image.objects_including_wip.all())
        if image is None:
            raise Http404

        item = get_object_or_404(klass, pk=pk)

        return self.render_json_response({
            'html': render_to_string('popover/item.html', {
                'item': item,
                'item_type': item_type,
                'item_content_type': ContentType.objects.get_for_model(item),
                'image': image,
                'REQUEST_COUNTRY': get_client_country_code(request),
                'search_query': request.GET.get('q', ''),
                'request': request,
                'BETA_TESTERS_GROUP_NAME': GroupName.BETA_TESTERS,
            })
        })
