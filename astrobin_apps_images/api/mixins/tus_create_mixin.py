import json

import simplejson
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from rest_framework import mixins, status

from astrobin_apps_images.api import constants
from astrobin_apps_images.api.mixins import TusCacheMixin
from astrobin_apps_images.api.utils import has_required_tus_header, add_expiry_header, decode_upload_metadata, \
    apply_headers_to_response


class TusCreateMixin(TusCacheMixin, mixins.CreateModelMixin):
    def create(self, request, *args, **kwargs):
        # Validate tus header
        if not has_required_tus_header(request):
            return HttpResponse('Missing "{}" header.'.format('Tus-Resumable'), status=status.HTTP_400_BAD_REQUEST)

        # Get file size from request
        upload_length = int(request.META.get(constants.UPLOAD_LENGTH_FIELD_NAME, -1))

        # Validate upload_length
        max_file_size = getattr(self, 'max_file_size', constants.TUS_MAX_FILE_SIZE)
        if upload_length > max_file_size:
            return HttpResponse('Invalid "Upload-Length". Maximum value: {}.'.format(max_file_size),
                                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # If upload_length is not given, we expect the defer header!
        if not upload_length or upload_length < 0:
            if getattr(request, constants.UPLOAD_DEFER_LENGTH_FIELD_NAME, -1) != 1:
                return HttpResponse('Missing "{Upload-Defer-Length}" header.', status=status.HTTP_400_BAD_REQUEST)

        # Get metadata from request
        upload_metadata = decode_upload_metadata(request.META.get(constants.UPLOAD_METADATA_FIELD_NAME, {}))

        # Get data from metadata
        name = upload_metadata.get(constants.TUS_NAME_METADATA_FIELD, '')
        filename = upload_metadata.get(constants.TUS_FILENAME_METADATA_FIELD, '')

        # Validate the filename
        filename = self.validate_filename(filename)

        # Retrieve serializer
        serializer = self.get_serializer(data={
            'upload_length': upload_length,
            'upload_metadata': json.dumps(upload_metadata),
            'filename': filename,
            'title': upload_metadata['title'],
            'is_wip': upload_metadata['is_wip'] if 'is_wip' in upload_metadata else False,
            'skip_notifications': upload_metadata[
                'skip_notifications'] if 'skip_notifications' in upload_metadata else False,
            'user_id': request.user.id,
        })

        # Validate serializer
        serializer.is_valid(raise_exception=True)

        # Create upload object
        self.perform_create(serializer)

        # Get upload from serializer
        image = serializer.instance

        # Prepare response headers
        headers = self.get_success_headers(serializer.data)

        expiration = timezone.now() + constants.TUS_UPLOAD_EXPIRES

        self.set_cached_property("name", image, name)
        self.set_cached_property("filename", image, filename)
        self.set_cached_property("upload-length", image, upload_length)
        self.set_cached_property("offset", image, 0)
        self.set_cached_property("expires", image, expiration)
        self.set_cached_property("metadata", image, upload_metadata)

        # Add upload expiry to headers
        add_expiry_header(expiration, headers)

        # Validate headers
        headers = self.validate_success_headers(headers)

        # By default, don't include a response body
        if not constants.TUS_RESPONSE_BODY_ENABLED:
            response = HttpResponse(
                content_type='application/javascript',
                status=status.HTTP_201_CREATED)
            response = apply_headers_to_response(response, headers)
            return response

        response = HttpResponse(
            simplejson.dumps(serializer.data),
            content_type='application/javascript',
            status=status.HTTP_201_CREATED)
        response = apply_headers_to_response(response, headers)
        return response

    def get_success_headers(self, data):
        try:
            return {'Location': reverse('astrobin_apps_images:image-detail', kwargs={'pk': data['pk']})}
        except (TypeError, KeyError):
            return {}

    def validate_success_headers(self, headers):
        """
        Handler to validate success headers before the response is sent. Should throw a ValidationError if
          something's off.
        :param dict headers:
        :return dict: The headers
        """
        return headers

    def validate_filename(self, filename):
        """
        Handler to validate the filename. Should throw a ValidationError if something's off.
        :param six.text_type filename:
        :return six.text_type: The filename
        """
        return filename
