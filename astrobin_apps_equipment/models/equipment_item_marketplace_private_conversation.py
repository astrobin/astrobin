# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from safedelete.models import SafeDeleteModel


class EquipmentItemMarketplacePrivateConversation(SafeDeleteModel):
    user = models.ForeignKey(
        User,
        related_name='equipment_item_marketplace_listings_private_conversations',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    listing = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceListing',
        related_name='private_conversations',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        editable=False,
    )
    
    comments = GenericRelation(
        'nested_comments.NestedComment',
        related_query_name='equipment_item_marketplace_private_conversations',
    )

    def __str__(self):
        return f'Marketplace listing private conversation for {self.listing} by {self.user}: {self.amount}'
