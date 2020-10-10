from django.conf.urls import url

from astrobin_apps_images.feeds.ts_optics import TsOpticsFeed, TsOpticsAtomFeed

urlpatterns = (
    # Feeds
    url(r'rss/ts-optics', TsOpticsFeed(), name='images_rss_ts_optics'),
    url(r'atom/ts-optics', TsOpticsAtomFeed(), name='images_rss_atom_ts_optics'),
)
