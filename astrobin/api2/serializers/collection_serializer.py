from rest_framework import serializers

from astrobin.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    cover_thumbnail = serializers.SerializerMethodField()
    cover_thumbnail_hd = serializers.SerializerMethodField()
    square_cropping = serializers.SerializerMethodField()
    w = serializers.SerializerMethodField()
    h = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    user_display_name = serializers.CharField(source='user.userprofile.get_display_name', read_only=True)
    display_collections_on_public_gallery = serializers.BooleanField(
        source='user.userprofile.display_collections_on_public_gallery',
        read_only=True
    )

    def _get_cover_image(self, instance: Collection):
        return instance.cover or instance.images.first()

    def _get_cover_final_revision(self, instance: Collection):
        cover_image = self._get_cover_image(instance)

        if cover_image is None:
            return None

        from astrobin_apps_images.services import ImageService
        return ImageService(cover_image).get_final_revision()

    def _use_dynamic_data(self, instance: Collection):
        # We are post migration and the data is not there yet, serialize with live data
        return hasattr(instance, 'cover_thumbnail') and instance.cover_thumbnail is None

    def get_cover_thumbnail(self, instance: Collection):
        if self._use_dynamic_data(instance):
            cover = self._get_cover_image(instance)

            if cover is None:
                return None

            return self._get_cover_image(instance).thumbnail('regular', None, sync=True)

        return instance.cover_thumbnail

    def get_cover_thumbnail_hd(self, instance: Collection):
        if self._use_dynamic_data(instance):
            cover = self._get_cover_image(instance)

            if cover is None:
                return None

            return self._get_cover_image(instance).thumbnail('hd', None, sync=True)
        return instance.cover_thumbnail_hd

    def get_square_cropping(self, instance: Collection):
        if self._use_dynamic_data(instance):
            final_revision = self._get_cover_final_revision(instance)

            if final_revision is None:
                return '0,0,0,0'

            return final_revision.square_cropping

        return instance.square_cropping or '0,0,0,0'

    def get_w(self, instance: Collection):
        if self._use_dynamic_data(instance):
            final_revision = self._get_cover_final_revision(instance)

            if final_revision is None:
                return None

            return final_revision.w

        return instance.w

    def get_h(self, instance: Collection):
        if self._use_dynamic_data(instance):
            final_revision = self._get_cover_final_revision(instance)

            if final_revision is None:
                return None

            return final_revision.h

        return instance.h

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    class Meta:
        model = Collection
        exclude = ['images']
        read_only_fields = [
            'date_created',
            'date_updated',
            'user',
            'username',
            'user_display_name',
            'display_collections_on_public_gallery',
            'images',
            'cover',
            'image_count',
            'image_count_including_wip',
            'cover_thumbnail',
            'cover_thumbnail_hd',
            'w',
            'h',
            'square_cropping',
        ]
