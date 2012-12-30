# Python
import os

# Django
from django.utils.translation import ugettext as _

# Third party apps
from rest_framework import serializers

# This app
from .models import RawImage
from .utils import (
    md5_for_file,
    supported_raw_formats,
)


class RawImageSerializer(serializers.ModelSerializer):
    def validate_file(self, attrs, source):
        try:
            value = attrs[source]
        except KeyError:
            return attrs

        name, ext = os.path.splitext(value.name)
        if ext.lower().strip('.') not in supported_raw_formats():
            raise serializers.ValidationError(_('File type is not supported'))

        return attrs

    def validate(self, attrs):
        try:
            provided_hash = attrs['file_hash']
        except KeyError:
            return attrs

        real_hash = md5_for_file(attrs['file'].file)

        if provided_hash is not None and provided_hash != real_hash:
            raise serializers.ValidationError(
                "file_hash %s doesn't match uploaded file, whose hash is %s" %
                    (provided_hash, real_hash))
        return attrs

    class Meta:
        model = RawImage
        read_only_fields = (
            'user',
            'original_filename',
            'size',
            'uploaded',
            'indexed',
            'active',
            'image_type',
            'acquisition_date',
            'camera',
            'telescopeName',
            'filterName',
            'subjectName',
            'temperature',
        )

