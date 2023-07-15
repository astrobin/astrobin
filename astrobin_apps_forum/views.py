from typing import Optional

from django.shortcuts import redirect
from django.views import View
from pybb.views import TopicView

from astrobin_apps_forum.models import TopicRedirect


class RedirectTopicView(View):
    def get(self, request, *args, **kwargs):
        redirect_entry: Optional[TopicRedirect] = TopicRedirect.objects.filter(
            category_slug=kwargs['category_slug'],
            forum_slug=kwargs['forum_slug'],
            slug=kwargs['slug']
        ).first()

        if redirect_entry:
            return redirect('pybb:topic', pk=redirect_entry.topic.pk)
        else:
            topic_view = TopicView.as_view()
            return topic_view(request, *args, **kwargs)
