import json
from typing import Optional

from actstream.models import Action
from annoying.functions import get_object_or_None
from avatar.templatetags.avatar_tags import avatar_url
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from astrobin.models import Image, ImageRevision
from astrobin.stories import (
    ACTSTREAM_VERB_BOOKMARKED_IMAGE, ACTSTREAM_VERB_COMMENTED_IMAGE, ACTSTREAM_VERB_LIKED_IMAGE,
)
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing
from astrobin_apps_groups.models import Group


class FrontPageFeedSerializer(serializers.ModelSerializer):
    user_ct: ContentType
    image_ct: ContentType
    image_revision_ct: ContentType
    marketplace_listing_ct: ContentType
    group_ct: ContentType

    actor_display_name = serializers.SerializerMethodField()
    actor_username = serializers.SerializerMethodField()
    actor_avatar = serializers.SerializerMethodField()
    actor_content_type_name = serializers.CharField(source='actor_content_type.name', read_only=True)

    target_url = serializers.SerializerMethodField()
    target_display_name = serializers.SerializerMethodField()
    target_user_username = serializers.SerializerMethodField()
    target_user_display_name = serializers.SerializerMethodField()
    target_user_avatar = serializers.SerializerMethodField()

    action_object_url = serializers.SerializerMethodField()
    action_object_display_name = serializers.SerializerMethodField()
    action_object_user_username = serializers.SerializerMethodField()
    action_object_user_display_name = serializers.SerializerMethodField()
    action_object_user_avatar = serializers.SerializerMethodField()

    image = serializers.SerializerMethodField()
    image_w = serializers.SerializerMethodField()
    image_h = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    others_count = serializers.SerializerMethodField()

    data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.user_ct = ContentType.objects.get_for_model(User)
        self.image_ct = ContentType.objects.get_for_model(Image)
        self.image_revision_ct = ContentType.objects.get_for_model(ImageRevision)
        self.marketplace_listing_ct = ContentType.objects.get_for_model(EquipmentItemMarketplaceListing)
        self.group_ct = ContentType.objects.get_for_model(Group)

    def get_actor_display_name(self, obj) -> Optional[str]:
        return self._get_user_display_name(obj.actor_content_type, obj.actor)

    def get_actor_username(self, obj) -> Optional[str]:
        return self._get_user_username(obj.actor_content_type, obj.actor)

    def get_actor_avatar(self, obj) -> Optional[str]:
        return self._get_user_avatar(obj.actor_content_type, obj.actor)

    def get_target_display_name(self, obj) -> Optional[str]:
        if self._is_user(obj.target_content_type):
            return obj.target.userprofile.get_display_name()

        if self._is_image(obj.target_content_type):
            return obj.target.title

        if self._is_image_revision(obj.target_content_type):
            return obj.target.image.title + f' ({obj.target.label})'

        if self._is_marketplace_listing(obj.target_content_type):
            return obj.target.title

        if self._is_group(obj.target_content_type):
            return obj.target.name

        return None

    def get_target_url(self, obj) -> Optional[str]:
        return self._get_url(obj.target_content_type, obj.target)

    def get_target_user_username(self, obj) -> Optional[str]:
        return self._get_user_username(obj.target_content_type, obj.target)

    def get_target_user_display_name(self, obj) -> Optional[str]:
        return self._get_user_display_name(obj.target_content_type, obj.target)

    def get_target_user_avatar(self, obj) -> Optional[str]:
        return self._get_user_avatar(obj.target_content_type, obj.target)

    def get_action_object_display_name(self, obj) -> Optional[str]:
        if self._is_user(obj.action_object_content_type):
            return obj.action_object.userprofile.get_display_name()

        if self._is_image(obj.action_object_content_type):
            return obj.action_object.title

        if self._is_image_revision(obj.action_object_content_type):
            return obj.action_object.image.title + f' ({obj.action_object.label})'

        if self._is_marketplace_listing(obj.action_object_content_type):
            return obj.action_object.title

        if self._is_group(obj.action_object_content_type):
            return obj.action_object.name

        return None

    def get_action_object_url(self, obj) -> Optional[str]:
        return self._get_url(obj.action_object_content_type, obj.action_object)

    def get_action_object_user_username(self, obj) -> Optional[str]:
        return self._get_user_username(obj.action_object_content_type, obj.action_object)

    def get_action_object_user_display_name(self, obj) -> Optional[str]:
        return self._get_user_display_name(obj.action_object_content_type, obj.action_object)

    def get_action_object_user_avatar(self, obj) -> Optional[str]:
        return self._get_user_avatar(obj.action_object_content_type, obj.action_object)

    def get_image(self, obj) -> Optional[str]:
        for content_type, object_id in [
            (obj.action_object_content_type, obj.action_object_object_id),
            (obj.target_content_type, obj.target_object_id)
        ]:
            # Check for Image
            if self._is_image(content_type):
                image = get_object_or_None(Image.objects_including_wip_plain, pk=object_id)
                if image:
                    return image.thumbnail('hd', None, sync=True)

            # Check for ImageRevision
            if self._is_image_revision(content_type):
                revision = get_object_or_None(ImageRevision.objects, pk=object_id)
                if revision:
                    return revision.thumbnail('hd', sync=True)

            # Check for EquipmentItemMarketplaceListing
            if content_type == self.marketplace_listing_ct:
                listing = get_object_or_None(EquipmentItemMarketplaceListing.objects, pk=object_id)
                if listing:
                    line_item = listing.line_items.first()
                    if line_item:
                        image = line_item.images.first()
                        if image:
                            return image.thumbnail_file.url

        return None

    def get_image_w(self, obj) -> Optional[int]:
        for content_type, object_id in [
            (obj.action_object_content_type, obj.action_object_object_id),
            (obj.target_content_type, obj.target_object_id)
        ]:
            # Check for Image
            if self._is_image(content_type):
                image = get_object_or_None(Image.objects_including_wip_plain, pk=object_id)
                if image:
                    return image.w

            # Check for ImageRevision
            elif self._is_image_revision(content_type):
                revision = get_object_or_None(ImageRevision.objects, pk=object_id)
                if revision:
                    return revision.w

            # Check for EquipmentItemMarketplaceListing
            elif content_type == self.marketplace_listing_ct:
                listing = get_object_or_None(EquipmentItemMarketplaceListing.objects, pk=object_id)
                if listing:
                    line_item = listing.line_items.first()
                    if line_item:
                        image = line_item.images.first()
                        if image:
                            return image.w

            elif self._is_group(content_type):
                return 460

        return None

    def get_image_h(self, obj) -> Optional[int]:
        for content_type, object_id in [
            (obj.action_object_content_type, obj.action_object_object_id),
            (obj.target_content_type, obj.target_object_id)
        ]:
            # Check for Image
            if self._is_image(content_type):
                image = get_object_or_None(Image.objects_including_wip_plain, pk=object_id)
                if image:
                    return image.h

            # Check for ImageRevision
            elif self._is_image_revision(content_type):
                revision = get_object_or_None(ImageRevision.objects, pk=object_id)
                if revision:
                    return revision.h

            # Check for EquipmentItemMarketplaceListing
            elif content_type == self.marketplace_listing_ct:
                listing = get_object_or_None(EquipmentItemMarketplaceListing.objects, pk=object_id)
                if listing:
                    line_item = listing.line_items.first()
                    if line_item:
                        image = line_item.images.first()
                        if image:
                            return image.h

            elif self._is_group(content_type):
                return 320

        return None

    def get_thumbnail(self, obj) -> Optional[str]:
        for content_type, object_id in [
            (obj.action_object_content_type, obj.action_object_object_id),
            (obj.target_content_type, obj.target_object_id)
        ]:
            # Check for Image
            if self._is_image(content_type):
                image = get_object_or_None(Image.objects_including_wip_plain, pk=object_id)
                if image:
                    return image.thumbnail('gallery', None, sync=True)

            # Check for ImageRevision
            if self._is_image_revision(content_type):
                revision = get_object_or_None(ImageRevision.objects, pk=object_id)
                if revision:
                    return revision.thumbnail('gallery', sync=True)

            # Check for EquipmentItemMarketplaceListing
            if content_type == self.marketplace_listing_ct:
                listing = get_object_or_None(EquipmentItemMarketplaceListing.objects, pk=object_id)
                if listing:
                    line_item = listing.line_items.first()
                    if line_item:
                        image = line_item.images.first()
                        if image:
                            return image.thumbnail_file.url

        return None

    def get_others_count(self, obj) -> Optional[int]:
        if obj.verb == ACTSTREAM_VERB_LIKED_IMAGE:
            return obj.action_object.like_count - 1
        if obj.verb == ACTSTREAM_VERB_COMMENTED_IMAGE:
            return obj.target.comment_count - 1
        if obj.verb == ACTSTREAM_VERB_BOOKMARKED_IMAGE:
            return obj.action_object.bookmark_count - 1

        return None

    def get_data(self, obj) -> Optional[dict]:
        if obj.data:
            return json.loads(obj.data)
        return None

    def _is_user(self, content_type: ContentType) -> bool:
        return content_type == self.user_ct

    def _is_image(self, content_type: ContentType) -> bool:
        return content_type == self.image_ct

    def _is_image_revision(self, content_type: ContentType) -> bool:
        return content_type == self.image_revision_ct

    def _is_marketplace_listing(self, content_type: ContentType) -> bool:
        return content_type == self.marketplace_listing_ct

    def _is_group(self, content_type: ContentType) -> bool:
        return content_type == self.group_ct

    def _get_url(self, content_type: ContentType, obj) -> Optional[str]:
        if obj is None:
            return None

        if self._is_user(content_type):
            return obj.get_absolute_url()

        if self._is_image(content_type):
            return obj.get_absolute_url()

        if self._is_image_revision(content_type):
            return obj.image.get_absolute_url()

        if self._is_marketplace_listing(content_type):
            return obj.get_absolute_url()

        return None

    def _get_user_username(self, content_type: ContentType, obj) -> Optional[str]:
        if obj is None:
            return None

        if self._is_user(content_type):
            return obj.username

        if self._is_image(content_type):
            return obj.user.username

        if self._is_image_revision(content_type):
            return obj.image.user.username

        if self._is_marketplace_listing(content_type):
            return obj.user.username

        return None

    def _get_user_display_name(self, content_type: ContentType, obj) -> Optional[str]:
        if obj is None:
            return None

        if self._is_user(content_type):
            return obj.userprofile.get_display_name()

        if self._is_image(content_type):
            return obj.user.userprofile.get_display_name()

        if self._is_image_revision(content_type):
            return obj.image.user.userprofile.get_display_name()

        if self._is_marketplace_listing(content_type):
            return obj.user.userprofile.get_display_name()

        return None

    def _get_user_avatar(self, content_type: ContentType, obj) -> Optional[str]:
        if obj is None:
            return None

        if self._is_user(content_type):
            return avatar_url(obj, 200)

        if self._is_image(content_type):
            return avatar_url(obj.user, 200)

        if self._is_image_revision(content_type):
            return avatar_url(obj.image.user, 200)

        if self._is_marketplace_listing(content_type):
            return avatar_url(obj.user, 200)

        return None

    class Meta:
        model = Action
        fields = '__all__'
