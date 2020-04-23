from django.conf import settings
from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy, reverse
from django.utils.feedgenerator import Atom1Feed

from astrobin_apps_iotd.services import IotdService
from common.feeds.extended_rss_feed import ExtendedRSSFeed


class TopPickFeed(Feed):
    feed_type = ExtendedRSSFeed
    title = "AstroBin's Top Pick feed"
    link = reverse_lazy('top_picks')

    def items(self):
        return IotdService().get_top_picks()[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
       item.description

    def item_author_name(self, item):
        return item.user.userprofile.get_display_name()

    def item_author_link(self, item):
        return settings.BASE_URL + reverse('user_page', args=(item.user.username,))

    def item_pubdate(self, item):
        return item.publikshed

    def item_content_encoded(self, item):
        url = item.thumbnail  ('regular', {'sync': True})
        return '<img src="{}" alt="{}"><br>{}, by <a href="{}">{}</a>'.format(
            url,
            item.title,
            item.title,
            reverse('user_page', args=(item.user.username,)),
            item.user.userprofile.get_display_name()
        )

    def item_extra_kwargs(self, item):
        return {'content_encoded': self.item_content_encoded(item)}


class TopPickAtomFeed(TopPickFeed):
    feed_type = Atom1Feed

    def item_subtitle(self, item):
        return super(TopPickFeed, self).item_description(item)
