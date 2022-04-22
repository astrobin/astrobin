from django.utils.translation import ugettext_lazy as _


class EquipmentItemService:
    item = None

    def __init__(self, item):
        self.item = item

    def get_type(self):
        return self.item.__class__.__name__.lower()

    def get_type_label(self):
        item_type = self.get_type()
        type_map = {
            'telescope': _('Telescope'),
            'camera': _('Camera'),
            'mount': _('Mount'),
            'filter': _('Filter'),
            'accessory': _('Accessory'),
            'software': _('Software'),
        }

        return type_map.get(item_type)
