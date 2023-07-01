from django.contrib import admin

from .models import TopicRedirect


class TopicRedirectAdmin(admin.ModelAdmin):
    list_display = ['category_slug', 'forum_slug', 'slug', 'topic', 'created_at']
    search_fields = ['topic__name', 'category_slug', 'forum_slug', 'slug']


admin.site.register(TopicRedirect, TopicRedirectAdmin)
