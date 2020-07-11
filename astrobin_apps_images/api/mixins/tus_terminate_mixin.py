from django.http import HttpResponse
from rest_framework import mixins, status


class TusTerminateMixin(mixins.DestroyModelMixin):
    def destroy(self, request, *args, **kwargs):
        # Retrieve object
        image = self.get_object()

        # Destroy object
        self.perform_destroy(image)

        return HttpResponse(status=status.HTTP_204_NO_CONTENT)
