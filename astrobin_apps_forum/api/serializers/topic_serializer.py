from pybb.models import Topic
from rest_framework import serializers


class TopicSerializer(serializers.ModelSerializer):
    read = serializers.SerializerMethodField()
    forum_name = serializers.CharField(source='forum.name', read_only=True)
    last_post_username = serializers.CharField(source='last_post.user.username', read_only=True)
    last_post_user_display_name = serializers.CharField(source='last_post.user.userprofile.get_display_name', read_only=True)
    last_post_timestamp = serializers.DateTimeField(source='last_post.created', read_only=True)
    last_post_id = serializers.IntegerField(source='last_post.id', read_only=True)

    def get_read(self, obj: Topic) -> bool:
        user = self.context['request'].user

        if not user.is_authenticated:
            return False

        return obj.readed_by.filter(pk=self.context['request'].user.pk).exists()

    class Meta:
        model = Topic
        exclude = [
            'readed_by'
        ]
