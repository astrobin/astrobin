# Third party apps
from rest_framework import serializers

# This app
from .models import RawImage
from .utils import md5_for_file


class RawImageSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        provided_hash = attrs['file_hash']
        real_hash = md5_for_file(attrs['file'].file)

        if provided_hash != real_hash:
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

