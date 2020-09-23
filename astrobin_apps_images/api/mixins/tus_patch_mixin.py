import os

import simplejson
from django.core.files import File
from django.http import HttpResponse
from rest_framework import mixins, status
from rest_framework.exceptions import MethodNotAllowed

from astrobin_apps_images.api import constants, signals
from astrobin_apps_images.api.constants import TUS_API_CHECKSUM_ALGORITHMS
from astrobin_apps_images.api.exceptions import Conflict
from astrobin_apps_images.api.mixins import TusCacheMixin
from astrobin_apps_images.api.parsers import TusUploadStreamParser
from astrobin_apps_images.api.utils import has_required_tus_header, checksum_matches, add_expiry_header, write_data, \
    get_or_create_temporary_file, apply_headers_to_response


class TusPatchMixin(TusCacheMixin, mixins.UpdateModelMixin):
    def get_file_field_name(self):
        raise NotImplementedError

    def get_upload_path_function(self):
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
            return HttpResponse('Missing "{}" header.'.format('Tus-Resumable'), status=status.HTTP_400_BAD_REQUEST)

        # Validate content type
        if not self._is_valid_content_type(request):
            return HttpResponse('Invalid value for "Content-Type" header: {}. Expected "{}".'.format(
                request.META['CONTENT_TYPE'], TusUploadStreamParser.media_type), status=status.HTTP_400_BAD_REQUEST)

        # Retrieve object
        object = self.get_object()

        # Get upload_offset
        upload_offset = int(request.META.get(constants.UPLOAD_OFFSET_NAME, 0))

        # Validate upload_offset
        if upload_offset != self.get_cached_property("offset", object):
            raise Conflict

        temporary_file = get_or_create_temporary_file(object)
        if not os.path.isfile(temporary_file):
            # Initial request in the series of PATCH request was handled on a different server instance.
            return HttpResponse(
                'Previous chunks not found on this server.',
                status=status.HTTP_423_LOCKED)

        # Get chunk from request
        chunk_bytes = self.get_chunk(request)

        # Check for data
        if not chunk_bytes:
            return HttpResponse('No data.', status=status.HTTP_400_BAD_REQUEST)

        # Check checksum  (http://tus.io/protocols/resumable-upload.html#checksum)
        upload_checksum = request.META.get(constants.UPLOAD_CHECKSUM_FIELD_NAME, None)
        if upload_checksum is not None:
            if upload_checksum[0] not in TUS_API_CHECKSUM_ALGORITHMS:
                return HttpResponse('Unsupported Checksum Algorithm: {}.'.format(
                    upload_checksum[0]), status=status.HTTP_400_BAD_REQUEST)
            elif not checksum_matches(
                    upload_checksum[0], upload_checksum[1], chunk_bytes):
                return HttpResponse('Checksum Mismatch.', status=460)

        # Run chunk validator
        chunk_bytes = self.validate_chunk(upload_offset, chunk_bytes)

        # Check for data
        if not chunk_bytes:
            return HttpResponse('No data. Make sure "validate_chunk" returns data.', status=status.HTTP_400_BAD_REQUEST)

        # Write file
        try:
            write_data(object, chunk_bytes)
        except Exception as e:
            return HttpResponse(str(e), status=status.HTTP_400_BAD_REQUEST)

        headers = {
            'Upload-Offset': self.get_cached_property("offset", object)
        }

        if self.get_cached_property("upload-length", object) == self.get_cached_property("offset", object):
            # Trigger signal
            signals.saving.send(object)

            # Save file
            temporary_file = get_or_create_temporary_file(object)
            getattr(object, self.get_file_field_name()).save(
                self.get_upload_path_function()(object, self.get_cached_property("name", object)),
                File(open(temporary_file))
            )

            signals.saved.send(object)

            # Clean up
            os.remove(temporary_file)
            signals.finished.send(object)

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
        return response

    def _is_valid_content_type(self, request):
        return request.META['CONTENT_TYPE'] == TusUploadStreamParser.media_type
