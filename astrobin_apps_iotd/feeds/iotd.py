from datetime import datetime

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy, reverse
from django.utils.feedgenerator import Atom1Feed

from astrobin_apps_iotd.services import IotdService
from common.feeds import ExtendedRSSFeed


class IotdFeed(Feed):
    feed_type = ExtendedRSSFeed
    title = "AstroBin's Image of the Day feed"
    link = reverse_lazy('iotd_archive')

    def items(self):
        return IotdService().get_iotds()[:10]

    def item_title(self, item):
        return item.image.title

    def item_description(self, item):
        return item.image.description

    def item_link(self, item):
        return settings.BASE_URL + reverse('image_detail', kwargs={
            'id': item.image.get_id()
        })

    def item_author_name(self, item):
        name = item.image.user.userprofile.get_display_name().encode('ascii', 'ignore').decode('ascii')
        if name == u'':
            name = item.image.user.username

        return name

    def item_author_link(self, item):
        return settings.BASE_URL + reverse('user_page', args=(item.image.user.username,))

    def item_pubdate(self, item):
        return datetime(item.date.year, item.date.month, item.date.day)

    def item_content_encoded(self, item):
        url = item.image.thumbnail('regular', {'sync': True})
        return '<img src="{}" alt="{}"><br>{}, by <a href="{}">{}</a>'.format(
            url,
            item.image.title,
            item.image.title,
            reverse('user_page', args=(item.image.user.username,)),
            self.item_author_name(item)
        )

    def item_extra_kwargs(self, item):
        return {'content_encoded': self.item_content_encoded(item)}


class IotdAtomFeed(IotdFeed):
    feed_type = Atom1Feed

    def item_subtitle(self, item):
        return super(IotdFeed, self).item_description(item)
