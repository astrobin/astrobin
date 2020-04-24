from django.conf.urls import url

from astrobin_apps_iotd.feeds.iotd import IotdFeed, IotdAtomFeed
from astrobin_apps_iotd.feeds.top_picks import TopPickFeed, TopPickAtomFeed
from astrobin_apps_iotd.views import IotdToggleSubmissionAjaxView, IotdSubmissionQueueView, IotdToggleVoteAjaxView, \
    IotdReviewQueueView, IotdToggleJudgementAjaxView, IotdJudgementQueueView, IotdArchiveView, \
    IotdSubmittersForImageAjaxView, IotdReviewersForImageAjaxView

urlpatterns = (
    # Submissions
    url(
        r'^toggle-submission-ajax/(?P<pk>\d+)/$',
        IotdToggleSubmissionAjaxView.as_view(),
        name='iotd_toggle_submission_ajax'),
    url(
        r'^submission-queue/$',
        IotdSubmissionQueueView.as_view(),
        name='iotd_submission_queue'),

    # Votes
    url(
        r'^toggle-vote-ajax/(?P<pk>\d+)/$',
        IotdToggleVoteAjaxView.as_view(),
        name='iotd_toggle_vote_ajax'),
    url(
        r'^review-queue/$',
        IotdReviewQueueView.as_view(),
        name='iotd_review_queue'),

    # Judgements
    url(
        r'^toggle-iotd-judgement-ajax/(?P<pk>\d+)/$',
        IotdToggleJudgementAjaxView.as_view(),
        name='iotd_toggle_judgement_ajax'),
    url(
        r'^judgement-queue/$',
        IotdJudgementQueueView.as_view(),
        name='iotd_judgement_queue'),

    # Archive
    url(
        r'^archive/$',
        IotdArchiveView.as_view(),
        name='iotd_archive'),

    # Utils
    url(
        r'^submitters-for-image-ajax/(?P<pk>\d+)/$',
        IotdSubmittersForImageAjaxView.as_view(),
        name='iotd_submitters_for_image'),
    url(
        r'^reviewers-for-image-ajax/(?P<pk>\d+)/$',
        IotdReviewersForImageAjaxView.as_view(),
        name='iotd_reviewers_for_image'),

    # Feeds
    url(r'rss/iotd', IotdFeed(), name='iotd_rss_iotd'),
    url(r'atom/iotd', IotdAtomFeed(), name='iotd_atom_iotd'),
    url(r'rss/top-picks', TopPickFeed(), name='iotd_rss_top_picks'),
    url(r'atom/top-picks', TopPickAtomFeed(), name='iotd_atom_top_picks')
)
