from django.contrib.auth.models import User
from rest_framework import viewsets

from astrobin.models import Collection, Image
from astrobin_apps_images.api.serializers.image_fancybox_serializer import ImageFancyboxSerializer
from astrobin_apps_users.services import UserService
from common.permissions import ReadOnly


class UserFancyboxListViewSet(viewsets.ModelViewSet):
    serializer_class = ImageFancyboxSerializer
    permission_classes = [ReadOnly]
    pagination_class = None
    http_method_names = ["get", "options", "head"]

    def get_queryset(self):
        if 'user' in self.request.GET:
            user_pk = self.request.GET.get('user')
        elif self.request.user.is_authenticated:
            user_pk = self.request.user.pk
        else:
            return Image.objects.none()

        try:
            user: User = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            return Image.objects.none()

        user_service = UserService(user)
        include_wip = user_service.display_wip_images_on_public_gallery() and self.request.user == user

        subsection = self.request.GET.get('subsection') or 'uploaded'
        active = self.request.GET.get('active')
        use_union = subsection in ['uploaded', 'title']  # Only for subsections that don't require additional filtering.

        if include_wip:
            images = user_service.get_all_images(use_union)
        else:
            images = user_service.get_public_images(use_union)

        if 'staging' in self.request.GET and self.request.GET.get('staging') == '1':
            images = user_service.get_wip_images(use_union)

        if 'collection' in self.request.GET and self.request.GET.get('collection') != '':
            try:
                collection: Collection = Collection.objects.get(pk=self.request.GET.get('collection'))
            except Collection.DoesNotExist:
                return Image.objects.none()

            images = collection.images.all()

            if collection.order_by_tag:
                images = images \
                    .filter(keyvaluetags__key=collection.order_by_tag) \
                    .order_by("keyvaluetags__value")

            return images

        return user_service.sort_gallery_by(
            images,
            subsection,
            active
        )[0]

