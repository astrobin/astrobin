from rest_framework import serializers


class BaseQueueSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    pk = serializers.IntegerField(read_only=True)
    hash = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    image_file = serializers.CharField(read_only=True)
    video_file = serializers.CharField(read_only=True)
    encoded_video_file = serializers.CharField(read_only=True)
    loop_video = serializers.BooleanField(read_only=True)
    w = serializers.IntegerField(read_only=True)
    h = serializers.IntegerField(read_only=True)
    imaging_telescopes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    imaging_cameras = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    imaging_telescopes_2 = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    imaging_cameras_2 = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    published = serializers.DateTimeField(read_only=True)
    submitted_for_iotd_tp_consideration = serializers.DateTimeField(read_only=True)
