from rest_framework import serializers

from astrobin.models import CameraRenameProposal


class CameraRenameProposalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraRenameProposal
        fields = '__all__'
