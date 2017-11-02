# Python
import os

# Django
from django.utils.translation import ugettext as _

# Third party apps
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, UnsupportedMediaType

# This app
from .models import RawImage
from .utils import (
    md5_for_file,
    rawdata_supported_raw_formats,
    rawdata_user_used_percent,
)


class RawImageSerializer(serializers.ModelSerializer):
    def validate_file(self, value):
        name, ext = os.path.splitext(value.name)
        stripped_ext = ext.lower().strip('.')
        if stripped_ext not in rawdata_supported_raw_formats():
            raise UnsupportedMediaType(stripped_ext)

        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if rawdata_user_used_percent(user) >= 100:
            raise PermissionDenied(
                _("You don't have any free space on AstroBin Rawdata. Consider upgrading your account."))

        try:
            provided_hash = self.initial_data['file_hash']
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
        fields = '__all__'
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
