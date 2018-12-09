import uuid


def brand_logo_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return "equipment/brands/logos/%s.%s" % (uuid.uui4(), ext)


def equipment_item_photo_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    return "equipment/items/photos/%s.%s" % (uuid.uui4(), ext)
