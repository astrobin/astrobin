import json

from django.http import Http404
from rest_framework import status
from rest_framework.response import Response

from astrobin_apps_images.api.mixins import TusCacheMixin
from astrobin_apps_images.api.utils import has_required_tus_header, add_expiry_header, encode_upload_metadata


class TusHeadMixin(TusCacheMixin, object):
    def info(self, request, *args, **kwargs):
        # Validate tus header
        if not has_required_tus_header(request):
            return Response('Missing "{}" header.'.format('Tus-Resumable'), status=status.HTTP_400_BAD_REQUEST)

        try:
            image = self.get_object()
        except Http404:
            # Instead of simply trowing a 404, we need to add a cache-control header to the response
            return Response('Not found.', headers={'Cache-Control': 'no-store'}, status=status.HTTP_404_NOT_FOUND)

        headers = {
            'Upload-Offset': self.get_cached_property("offset", image),
            'Cache-Control': 'no-store'
        }

        if self.get_cached_property("upload-length", image) >= 0:
            headers['Upload-Length'] = image.upload_length

        if self.get_cached_property("metadata", image):
            headers['Upload-Metadata'] = encode_upload_metadata(json.loads(image.upload_metadata))

        # Add upload expiry to headers
        add_expiry_header("tus-uploads/{}/expires".format(image.pk), headers)

        return Response(headers=headers, status=status.HTTP_200_OK)
