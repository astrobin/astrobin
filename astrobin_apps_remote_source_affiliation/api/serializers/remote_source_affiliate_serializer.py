from rest_framework import serializers

from astrobin_apps_remote_source_affiliation.models import RemoteSourceAffiliate


class RemoteSourceAffiliateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RemoteSourceAffiliate
        fields = (
            'code',
            'name',
            'url',
            'affiliation_start',
            'affiliation_expiration',
            'image_file',
            'created',
            'updated',
        )
