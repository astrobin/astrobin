from django.db import models
from pybb.models import Topic


class TopicRedirect(models.Model):
    category_slug = models.CharField(max_length=255)
    forum_slug = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='redirects')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Topic redirect'
        verbose_name_plural = 'Topic redirects'
        unique_together = ('category_slug', 'forum_slug', 'slug')
        ordering = ('-created_at',)

    def __str__(self):
        return f'Redirect for Topic {self.topic.id} on {self.created_at}'
