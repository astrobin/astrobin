import logging

from django.http import Http404
from rest_framework import status
from rest_framework.response import Response

from astrobin_apps_images.api.mixins import TusCacheMixin
from astrobin_apps_images.api.utils import has_required_tus_header, add_expiry_header, encode_upload_metadata

log = logging.getLogger('apps')


class TusHeadMixin(TusCacheMixin, object):
    def head(self, request, *args, **kwargs):
        # Validate tus header
        if not has_required_tus_header(request):
            msg = 'Missing "{}" header.'.format('Tus-Resumable')
            log.warning("Chunked uploader (%s): %s" % (request.user, msg))
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        try:
            object = self.get_object()
        except Http404:
            # Instead of simply throwing a 404, we need to add a cache-control header to the response
            msg = 'Not found.'
            log.warning("Chunked uploader (%s): %s" % (request.user, msg))
            return Response(msg, headers={'Cache-Control': 'no-store'}, status=status.HTTP_404_NOT_FOUND)

        offset = self.get_cached_property("offset", object)

        if offset is None:
            offset = 0
            self.set_cached_property("offset", object, offset)

        headers = {
            'Upload-Offset': offset,
            'Cache-Control': 'no-store'
        }

        upload_metadata = self.get_cached_property("metadata", object)
        if upload_metadata:
            headers['Upload-Metadata'] = encode_upload_metadata(upload_metadata)

        # Add upload expiry to headers
        expiration = self.get_cached_property("expires", object)
        add_expiry_header(expiration, headers)

        return Response(headers=headers, status=status.HTTP_200_OK)
