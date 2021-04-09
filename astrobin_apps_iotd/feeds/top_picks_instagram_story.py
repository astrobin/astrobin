from django.utils.feedgenerator import Atom1Feed

from astrobin_apps_iotd.feeds.top_picks import TopPickFeed


class TopPickInstagramStoryFeed(TopPickFeed):
    def item_thumbnail_url(self, item):
        return item.image.thumbnail('instagram_story', None, sync=True)


class TopPickInstagramStoryAtomFeed(TopPickInstagramStoryFeed):
    feed_type = Atom1Feed

    def item_subtitle(self, item):
        return super(TopPickInstagramStoryAtomFeed, self).item_description(item)
