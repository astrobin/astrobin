from rest_framework import serializers

from astrobin.forms.utils import parseKeyValueTags
from astrobin_apps_images.models import KeyValueTag


class KeyValueTagsSerializerField(serializers.Field):
    def to_representation(self, obj):
        tags = obj.all()
        value = ""
        for tag in tags:
            value += "%s=%s\r\n" % (tag.key, tag.value)

        return value.rstrip('\r\n')

    def to_internal_value(self, data):
        instance = self.parent.instance
        instance.keyvaluetags.all().delete()
        value = []

        if data is None:
            return value

        for tag in parseKeyValueTags(data):
            value.append(KeyValueTag.objects.create(
                image=instance,
                key=tag["key"],
                value=tag["value"]
            ))

        return value
