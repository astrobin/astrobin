class EquipmentItemService:
    item = None

    def __init__(self, item):
        self.item = item

    def get_type(self):
        return self.item.__class__.__name__.lower()
