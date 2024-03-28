from django.utils.translation import ugettext_lazy as _

EQUIPMENT_NOTICE_TYPES = (
    ('equipment-item-requires-moderation', _('A new equipment item requires moderation'), '', 2),
    ('equipment-item-approved', _('Equipment item you created was approved'), '', 2),
    ('equipment-item-assigned', _('Equipment item was assigned to you'), '', 2),
    ('equipment-item-rejected', _('Equipment item you created was rejected'), '', 2),
    ('equipment-item-rejected-affected-image', _('Rejected equipment item removed from your image'), '', 2),
    ('equipment-edit-proposal-created', _('Equipment item received an edit proposal'), '', 2),
    ('equipment-edit-proposal-approved', _('Your edit proposal was approved'), '', 2),
    ('equipment-edit-proposal-assigned', _('Edit proposal assigned to you'), '', 2),
    ('equipment-edit-proposal-rejected', _('Your edit proposal was rejected'), '', 2),
    ('equipment-item-migration-approved', _('Approved migration proposal of an equipment item'), '', 2),
    ('equipment-item-migration-rejected', _('Rejected migration proposal of an equipment item'), '', 2),
    ('ambiguous-item-removed-from-presets', _('Ambiguous equipment item removed from presets'), '', 2),
    ('new-image-from-followed-equipment', _('New image from followed equipment item'), '', 2),
    ('marketplace-offer-created', _('New offer for your marketplace listing'), '', 2),
    ('marketplace-offer-updated', _('Offer for your marketplace listing got updated'), '', 2),
    ('marketplace-offer-accepted-by-seller', _('Marketplace offer accepted by seller'), '', 2),
    ('marketplace-offer-accepted-by-you', _('Marketplace offer accepted by you'), '', 2),
    ('marketplace-offer-rejected-by-seller', _('Marketplace offer rejected by seller'), '', 2),
    ('marketplace-offer-retracted', _('Marketplace offer retracted by buyer'), '', 2),
)
