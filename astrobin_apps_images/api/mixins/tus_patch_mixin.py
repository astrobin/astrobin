import logging
import os

import simplejson
from PIL import Image as PILImage
from django.core.files import File
from django.http import HttpResponse
from rest_framework import mixins, status
from rest_framework.exceptions import MethodNotAllowed
from safedelete import HARD_DELETE
from safedelete.models import SafeDeleteModel

from astrobin_apps_images.api import constants, signals
from astrobin_apps_images.api.constants import TUS_API_CHECKSUM_ALGORITHMS
from astrobin_apps_images.api.mixins import TusCacheMixin
from astrobin_apps_images.api.parsers import TusUploadStreamParser
from astrobin_apps_images.api.utils import (
    add_expiry_header, apply_headers_to_response, checksum_matches,
    get_or_create_temporary_file, has_required_tus_header, write_data,
)
from common.exceptions import Conflict

log = logging.getLogger(__name__)


class TusPatchMixin(TusCacheMixin, mixins.UpdateModelMixin):
    def clear_cache(self, obj):
        self.clear_cached_property("name", obj)
        self.clear_cached_property("filename", obj)
        self.clear_cached_property("upload-length", obj)
        self.clear_cached_property("offset", obj)
        self.clear_cached_property("expires", obj)
        self.clear_cached_property("metadata", obj)

    def delete_object(self, obj):
        delete_kwargs = {}
        if issubclass(type(obj), SafeDeleteModel):
            delete_kwargs['force_policy'] = HARD_DELETE
        obj.delete(**delete_kwargs)

    def get_file_field_name(self, mime_type: str) -> str:
        raise NotImplementedError

    def get_upload_path_function(self, mime_type: str):
        raise NotImplementedError

    def verify_file(self, file_path: str, mime_type: str) -> bool:
        raise NotImplementedError

    def get_chunk(self, request):
        if TusUploadStreamParser in self.parser_classes:
            return request.data['chunk']
        return request.body

    def validate_chunk(self, offset, chunk_bytes):
        """
        Handler to validate chunks before they are actually written to the buffer file. Should throw a ValidationError
          if something's off.
        :param int offset:
        :param six.binary_type chunk_bytes:
        :return six.binary_type: The chunk_bytes
        """
        return chunk_bytes

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed

    def partial_update(self, request, *args, **kwargs):
        # Validate tus header
        if not has_required_tus_header(request):
            msg = 'Missing "{}" header.'.format('Tus-Resumable')
            log.warning("Chunked uploader (%d): %s" % (request.user.pk, msg))
            return HttpResponse(msg, status=status.HTTP_400_BAD_REQUEST)

        # Validate content type
        if not self._is_valid_content_type(request):
            msg = 'Invalid value for "Content-Type" header: {}. Expected "{}".'.format(
                request.META['CONTENT_TYPE'], TusUploadStreamParser.media_type)
            log.warning("Chunked uploader (%d): %s" % (request.user.pk, msg))
            return HttpResponse(msg, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve object
        object = self.get_upload_in_progress_object() \
            if hasattr(self, 'get_upload_in_progress_object') \
            else self.get_object()

        # Get upload_offset
        upload_offset = int(request.META.get(constants.UPLOAD_OFFSET_NAME, 0))

        # Validate upload_offset
        if upload_offset != self.get_cached_property("offset", object):
            log.warning("Chunked uploader (%d) (%d): offset conflict" % (request.user.pk, object.pk))
            self.delete_object(object)
            raise Conflict

        temporary_file = get_or_create_temporary_file(object)
        if not os.path.isfile(temporary_file):
            # Initial request in the series of PATCH request was handled on a different server instance.
            msg = 'Previous chunks not found on this server.'
            log.warning("Chunked uploader (%d) (%d): %s" % (request.user.pk, object.pk, msg))
            return HttpResponse(msg, status=status.HTTP_423_LOCKED)

        # Get chunk from request
        chunk_bytes = self.get_chunk(request)

        # Check for data
        if not chunk_bytes:
            msg = 'No data.'
            log.warning("Chunked uploader (%d) (%d): %s" % (request.user.pk, object.pk, msg))
            self.delete_object(object)
            return HttpResponse(msg, status=status.HTTP_400_BAD_REQUEST)

        # Check checksum (http://tus.io/protocols/resumable-upload.html#checksum)
        upload_checksum = request.META.get(constants.UPLOAD_CHECKSUM_FIELD_NAME, None)
        if upload_checksum is not None:
            if upload_checksum[0] not in TUS_API_CHECKSUM_ALGORITHMS:
                msg = 'Unsupported Checksum Algorithm: {}.'.format(upload_checksum[0])
                log.warning("Chunked uploader (%d) (%d): %s" % (request.user.pk, object.pk, msg))
                self.delete_object(object)
                return HttpResponse(msg, status=status.HTTP_400_BAD_REQUEST)
            elif not checksum_matches(upload_checksum[0], upload_checksum[1], chunk_bytes):
                msg = 'Checksum Mismatch.'
                log.warning("Chunked uploader (%d) (%d) : %s" % (request.user.pk, object.pk, msg))
                self.delete_object(object)
                return HttpResponse(msg, status=460)

        # Run chunk validator
        chunk_bytes = self.validate_chunk(upload_offset, chunk_bytes)

        # Check for data
        if not chunk_bytes:
            msg = 'No data. Make sure "validate_chunk" returns data.'
            log.warning("Chunked uploader (%d) (%d): %s" % (request.user.pk, object.pk, msg))
            self.delete_object(object)
            return HttpResponse(msg, status=status.HTTP_400_BAD_REQUEST)

        # Write file
        try:
            write_data(object, chunk_bytes)
            log.debug("Chunked uploader (%d) (%d): wrote %d bytes" % (request.user.pk, object.pk, len(chunk_bytes)))
        except Exception as e:
            msg = str(e)
            log.warning("Chunked uploader (%d) (%d): exception writing data: %s" % (request.user.pk, object.pk, msg))
            self.delete_object(object)
            return HttpResponse(msg, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            'Upload-Offset': self.get_cached_property("offset", object)
        }

        if self.get_cached_property("upload-length", object) == self.get_cached_property("offset", object):
            log.debug("Chunked uploader (%d) (%d): chunks completed" % (request.user.pk, object.pk))

            # Trigger signal
            signals.saving.send(object)

            # Save file
            temporary_file = get_or_create_temporary_file(object)

            metadata = self.get_cached_property("metadata", object)
            mime_type = metadata.get('mimeType', None)

            if not self.verify_file(temporary_file, mime_type):
                msg = "file verification failed"
                log.warning("Chunked uploader (%d) (%d): %s" % (request.user.pk, object.pk, msg))
                os.remove(temporary_file)
                self.delete_object(object)
                return HttpResponse(msg, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

            log.debug("Chunked uploader (%d) (%d): saving object to temporary file %s" % (
                request.user.pk, object.pk, temporary_file))

            try:
                attr = getattr(object, self.get_file_field_name(mime_type))
                filename = self.get_upload_path_function(mime_type)(object, self.get_cached_property("name", object))
                with open(temporary_file, 'rb') as opened_temporary_file:
                    attr.save(filename, File(opened_temporary_file))

                if hasattr(object, 'animated') and mime_type.startswith('image'):
                    with PILImage.open(temporary_file) as image_file:
                        object.animated = getattr(image_file, 'is_animated', False)

                if hasattr(object, 'uploader_in_progress'):
                    object.uploader_in_progress = None

                    save_kwargs = {}
                    if issubclass(type(object), SafeDeleteModel):
                        save_kwargs['keep_deleted'] = True
                    object.save(**save_kwargs)
            except Exception as e:
                log.error("Chunked uploader (%d) (%d): exception: %s" % (
                    request.user.pk, object.pk, str(e)
                ))
                os.remove(temporary_file)
                self.delete_object(object)
                return HttpResponse(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            signals.saved.send(object)

            # Clean up
            os.remove(temporary_file)
            signals.finished.send(object)

            log.debug("Chunked uploader (%d) (%d): finished" % (request.user.pk, object.pk))

        # Add upload expiry to headers
        add_expiry_header(self.get_cached_property("expires", object), headers)

        # By default, don't include a response body
        if not constants.TUS_RESPONSE_BODY_ENABLED:
            response = HttpResponse(
                content_type='application/javascript',
                status=status.HTTP_201_CREATED)

            response = apply_headers_to_response(response, headers)

            return response

        # Create serializer
        serializer = self.get_serializer(instance=object)

        response = HttpResponse(
            simplejson.dumps(serializer.data),
            content_type='application/javascript',
            status=status.HTTP_201_CREATED)

        response = apply_headers_to_response(response, headers)

        if self.get_cached_property("upload-length", object) == self.get_cached_property("offset", object):
            self.clear_cache(object)

        return response

    def _is_valid_content_type(self, request):
        return request.META['CONTENT_TYPE'] == TusUploadStreamParser.media_type
