from pybb.models import Topic

from common.services.forum_service import ForumService


class PreviousTopicReadMarkerMiddleware(object):
    def process_request(self, request):
        if not request.path.startswith('/forum/c/'):
            return

        parts = request.path.split('/')

        if len(parts) < 6:
            return

        category_slug = parts[3]
        forum_slug = parts[4]
        topic_slug = parts[5]

        if not topic_slug:
            return

        try:
            topic = Topic.objects.get(
                slug=topic_slug,
                forum__slug=forum_slug,
                forum__category__slug=category_slug
            )
            first_unread = ForumService.get_topic_first_unread(topic, request.user)

            if first_unread:
                request.session['first_unread_for_topic_%d' % topic.pk] = first_unread.created.isoformat()
                request.session['first_unread_for_topic_%d_post' % topic.pk] = first_unread.pk
            else:
                try:
                    del request.session['first_unread_for_topic_%d' % topic.pk]
                except KeyError:
                    pass

                try:
                    del request.session['first_unread_for_topic_%d_post' % topic.pk]
                except KeyError:
                    pass
        except Topic.DoesNotExist:
            return
