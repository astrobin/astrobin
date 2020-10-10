import os

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed

from astrobin.models import Image
from common.feeds.extended_rss_feed import ExtendedRSSFeed


class TsOpticsFeed(Feed):
    feed_type = ExtendedRSSFeed
    title = "TS Optics images on AstroBin"
    link = "/search"
    item_enclosure_length = 0  # Unknown

    def items(self):
        return Image.objects.filter(
            Q(imaging_telescopes__make__icontains='TS Optics') |
            Q(imaging_telescopes__make__icontains='TS-Optics') |
            Q(imaging_telescopes__make__iexact='TS')
        )[:10]

    def item_guid(self, item):
        return "%s" % item.get_id()

    def item_title(self, item):
        return item.title.encode('ascii', 'ignore').decode('ascii')

    def item_description(self, item):
        self.item_thumbnail_url(item)

    def item_link(self, item):
            return settings.BASE_URL + reverse('image_detail', kwargs={
            'id': item.get_id()
        })

    def item_author_name(self, item):
        name = item.user.userprofile.get_display_name().encode('ascii', 'ignore').decode('ascii')
        if name == u'':
            name = item.user.username.encode('ascii', 'ignore').decode('ascii')

        return name

    def item_author_link(self, item):
        return settings.BASE_URL + reverse('user_page', args=(item.user.username,))

    def item_pubdate(self, item):
        return item.published

    def item_thumbnail_url(self, item):
        return item.thumbnail('hd', {'sync': True})

    def item_enclosure_url(self, item):
        return self.item_thumbnail_url(item)

    def item_enclosure_mime_type(self, item):
        url = self.item_thumbnail_url(item)
        path, ext = os.path.splitext(url)

        if ext.lower() in ('.jpg', '.jpeg'):
            return 'image/jpeg'

        if ext.lower() == '.png':
            return 'image/png'

        if ext.lower() == '.gif':
            return 'image/gif'

        return 'application/octet-stream'

    def item_content_encoded(self, item):
        url = self.item_thumbnail_url(item)
        return '<img src="{}" alt="{}"><br>{}, by <a href="{}">{}</a><br>{}'.format(
            url,
            self.item_title(item),
            self.item_title(item),
            reverse('user_page', args=(item.user.username,)),
            self.item_author_name(item),
            item.description.encode('ascii', 'ignore').decode('ascii')
        )

    def item_extra_kwargs(self, item):
        return {
            'content_encoded': self.item_content_encoded(item),
        }


class TsOpticsAtomFeed(TsOpticsFeed):
    feed_type = Atom1Feed

    def item_subtitle(self, item):
        return super(TsOpticsFeed, self).item_description(item)
