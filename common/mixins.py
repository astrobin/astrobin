import simplejson as json

from django.http import HttpResponse

import logging
from io import BytesIO

from django.core.files.base import ContentFile
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer

logger = logging.getLogger(__name__)


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """

    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        if self.request.is_ajax():
            return self.render_to_json_response(form.errors, status=400)
        else:
            return super(AjaxableResponseMixin, self).form_invalid(form)

    def form_valid(self, form):
        if self.request.is_ajax():
            data = {
                'pk': form.instance.pk,
            }
            return self.render_to_json_response(data)
        else:
            return super(AjaxableResponseMixin, self).form_valid(form)


class RequestUserRestSerializerMixin(object):
    def create(self, validated_data):
        """Override ``create`` to provide a user via request.user by default.

        This is required since the read_only ``user`` field is not included by
        default anymore since https://github.com/encode/django-rest-framework/pull/5886.
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Override ``update`` to provide a user via request.user by default.

        This is required since the read_only ``user`` field is not included by
        default anymore since https://github.com/encode/django-rest-framework/pull/5886.
        """
        validated_data['user'] = self.context['request'].user
        return super().update(instance, validated_data)


class ThumbnailMixin:
    # Flag to prevent recursive thumbnail creation
    _creating_thumbnail = False

    # Override these in your model to customize field names
    image_field_name = 'image'
    thumbnail_field_name = 'thumbnail'

    def create_thumbnail(self):
        if self._creating_thumbnail:
            logger.debug('create_thumbnail: skipping thumbnail creation because it\'s already in progress')
            return

        image_field = getattr(self, self.image_field_name, None)
        if not image_field:
            logger.debug(f'create_thumbnail: skipping thumbnail creation because there is no {self.image_field_name}')
            return

        self._creating_thumbnail = True

        def _get_thumbnail_bytes(options):
            thumbnailer = get_thumbnailer(image_field)
            thumbnail = thumbnailer.get_thumbnail(options)

            thumb_io = BytesIO()
            thumb_io.write(thumbnail.read())
            thumb_io.seek(0)

            return thumbnail, thumb_io

        try:
            options = {
                'size': (512, 0),
                'crop': True,
                'keep_icc_profile': True,
                'quality': 80,
            }

            thumbnail, thumb_io = _get_thumbnail_bytes(options)

            if thumb_io.getbuffer().nbytes == 0:
                thumbnail, thumb_io = _get_thumbnail_bytes(options)
                if thumb_io.getbuffer().nbytes == 0:
                    logger.debug('create_thumbnail: skipping thumbnail creation because the image is invalid')
                    return

            thumbnail_field = getattr(self, self.thumbnail_field_name)
            thumbnail_field.save(thumbnail.name, ContentFile(thumb_io.getvalue()))
            thumb_io.close()

            logger.debug(f'create_thumbnail: thumbnail created successfully {thumbnail_field.url}')
        except InvalidImageFormatError:
            logger.debug('create_thumbnail: skipping thumbnail creation because the image is invalid')
        finally:
            self._creating_thumbnail = False
