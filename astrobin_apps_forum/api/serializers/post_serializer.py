from pybb.models import Post
from rest_framework import serializers


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['user', 'user_ip', 'on_moderation', 'body_text', 'body_html', 'created', 'updated']
