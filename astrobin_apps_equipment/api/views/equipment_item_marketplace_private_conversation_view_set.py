from django.contrib.auth.models import User
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.permissions.may_update_marketplace_private_conversation import \
    MayUpdateMarketplacePrivateConversation
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_private_conversation_serializer import \
    EquipmentItemMarketplacePrivateConversationSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing, EquipmentItemMarketplacePrivateConversation


class EquipmentItemMarketplacePrivateConversationViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [MayUpdateMarketplacePrivateConversation]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('id', 'user')
    serializer_class = EquipmentItemMarketplacePrivateConversationSerializer

    def get_queryset(self):
        listing_id = self.kwargs.get('listing_id')
        if listing_id is not None:
            # Check if the listing exists and raise 404 if not
            listing = get_object_or_404(EquipmentItemMarketplaceListing, pk=listing_id)

            if listing.user == self.request.user:
                return EquipmentItemMarketplacePrivateConversation.objects.filter(listing_id=listing_id)

            if self.request.user.is_authenticated:
                return EquipmentItemMarketplacePrivateConversation.objects.filter(
                    listing_id=listing_id, user=self.request.user
                )

            return EquipmentItemMarketplacePrivateConversation.objects.none()
        else:
            # Raise a 404 error if listing_id is not provided in the URL
            from django.http import Http404
            raise Http404("Listing ID not provided")

    def perform_create(self, serializer):
        listing_id = self.kwargs.get('listing_id')
        listing = get_object_or_404(EquipmentItemMarketplaceListing, pk=listing_id)
        user = self.request.user
        now = timezone.now()

        # Check if the user is the owner of the listing
        if user == listing.user and self.request.query_params.get('user') is not None:
            user = get_object_or_404(User, pk=self.request.query_params.get('user'))

        save_params = {
            'user': user,
            'listing': listing,
        }

        if user == listing.user:
            save_params['listing_user_last_accessed'] = now
        else:
            save_params['user_last_accessed'] = now

        serializer.save(**save_params)

    def destroy(self, request, *args, **kwargs):
        conversation: EquipmentItemMarketplacePrivateConversation = self.get_object()

        # Check if the current user is the owner of the conversation or the listing
        if request.user != conversation.user and request.user != conversation.listing.user:
            raise PermissionDenied("You do not have permission to delete this conversation.")

        if conversation.comments.count() > 0:
            raise PermissionDenied("You cannot delete a conversation with comments.")

        # If the user is the owner, proceed with the deletion
        return super(EquipmentItemMarketplacePrivateConversationViewSet, self).destroy(request, *args, **kwargs)