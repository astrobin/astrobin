from rest_framework import serializers

from astrobin.models import SavedSearch


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = (
            "id",
            "user",
            "name",
            "params",
            "created",
            "updated",
        )
        read_only_fields = (
            "id",
            "user",
            "created",
            "updated",
        )
