from django.conf.urls import url
from django.views.decorators.cache import never_cache

from astrobin_apps_iotd.feeds.iotd import IotdFeed, IotdAtomFeed
from astrobin_apps_iotd.feeds.top_picks import TopPickFeed, TopPickAtomFeed
from astrobin_apps_iotd.feeds.top_picks_instagram_story import TopPickInstagramStoryFeed, TopPickInstagramStoryAtomFeed
from astrobin_apps_iotd.views import IotdToggleJudgementAjaxView, IotdJudgementQueueView, IotdArchiveView, \
    IotdSubmissionQueueView, IotdReviewQueueView

urlpatterns = (
    # Submissions
    url(
        r'^submission-queue/$',
        never_cache(IotdSubmissionQueueView.as_view()),
        name='iotd_submission_queue'),

    # Votes
    url(
        r'^review-queue/$',
        never_cache(IotdReviewQueueView.as_view()),
        name='iotd_review_queue'),

    # Judgements
    url(
        r'^toggle-iotd-judgement-ajax/(?P<pk>\d+)/$',
        never_cache(IotdToggleJudgementAjaxView.as_view()),
        name='iotd_toggle_judgement_ajax'),
    url(
        r'^judgement-queue/$',
        never_cache(IotdJudgementQueueView.as_view()),
        name='iotd_judgement_queue'),

    # Archive
    url(
        r'^archive/$',
        never_cache(IotdArchiveView.as_view()),
        name='iotd_archive'),

    # Feeds
    url(r'rss/iotd$', IotdFeed(), name='iotd_rss_iotd'),
    url(r'atom/iotd$', IotdAtomFeed(), name='iotd_atom_iotd'),
    url(r'rss/top-picks$', TopPickFeed(), name='iotd_rss_top_picks'),
    url(r'atom/top-picks$', TopPickAtomFeed(), name='iotd_atom_top_picks'),
    url(r'rss/top-picks/instagram-story$', TopPickInstagramStoryFeed(), name = 'iotd_rss_top_picks_instagram_story'),
    url(r'atom/top-picks/instagram-story$', TopPickInstagramStoryAtomFeed(), name='iotd_atom_top_picks_instagram_story')
)
