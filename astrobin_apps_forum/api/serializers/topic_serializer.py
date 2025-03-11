from pybb.models import ForumReadTracker, Topic, TopicReadTracker
from rest_framework import serializers


class TopicSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.CharField(source='user.userprofile.get_display_name', read_only=True)
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

        topic_tracker = TopicReadTracker.objects.filter(user=user, topic=obj).first()

        if topic_tracker:
            return topic_tracker.time_stamp >= obj.updated
        else:
            forum_tracker = ForumReadTracker.objects.filter(user=user, forum=obj.forum).first()
            if forum_tracker:
                return forum_tracker.time_stamp >= obj.updated

        return False

    class Meta:
        model = Topic
        exclude = [
            'readed_by'
        ]
