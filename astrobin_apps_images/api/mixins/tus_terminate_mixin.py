from django.http import HttpResponse
from rest_framework import mixins, status


class TusTerminateMixin(mixins.DestroyModelMixin):
    def destroy(self, request, *args, **kwargs):
        # Retrieve object
        image = self.get_object()

        # Destroy object
        self.perform_destroy(image)

        self.clear_cached_property("name", object)
        self.clear_cached_property("filename", object)
        self.clear_cached_property("upload-length", object)
        self.clear_cached_property("offset", object)
        self.clear_cached_property("expires", object)
        self.clear_cached_property("metadata", object)

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
