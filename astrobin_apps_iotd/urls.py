from django.conf.urls import url

from astrobin_apps_iotd.feeds.iotd import IotdAtomFeed, IotdFeed
from astrobin_apps_iotd.feeds.top_picks import TopPickAtomFeed, TopPickFeed
from astrobin_apps_iotd.feeds.top_picks_instagram_story import TopPickInstagramStoryAtomFeed, TopPickInstagramStoryFeed
from astrobin_apps_iotd.views import IotdArchiveView

urlpatterns = (
    # Archive
    url(
        r'^archive/$',
        IotdArchiveView.as_view(),
        name='iotd_archive'
    ),

    # Feeds
    url(r'rss/iotd$', IotdFeed(), name='iotd_rss_iotd'),
    url(r'atom/iotd$', IotdAtomFeed(), name='iotd_atom_iotd'),
    url(r'rss/top-picks$', TopPickFeed(), name='iotd_rss_top_picks'),
    url(r'atom/top-picks$', TopPickAtomFeed(), name='iotd_atom_top_picks'),
    url(r'rss/top-picks/instagram-story$', TopPickInstagramStoryFeed(), name = 'iotd_rss_top_picks_instagram_story'),
    url(r'atom/top-picks/instagram-story$', TopPickInstagramStoryAtomFeed(), name='iotd_atom_top_picks_instagram_story')
)
