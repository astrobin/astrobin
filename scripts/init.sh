#!/bin/sh

# Collect static files
python manage.py collectstatic --noinput

# Migrate
python manage.py migrate --noinput
python manage.py migrate --run-syncdb --noinput

# Create initial data
python manage.py shell << EOF
from common.constants import GroupName
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site

from cookie_consent.models import CookieGroup, Cookie
from pybb.models import Category, Forum
from subscription.models import Subscription

from astrobin_apps_premium.services.premium_service import SubscriptionName

Group.objects.get_or_create(name='astrobin_lite')
Group.objects.get_or_create(name='astrobin_lite_2020')
Group.objects.get_or_create(name='astrobin_premium')
Group.objects.get_or_create(name='astrobin_premium_2020')
Group.objects.get_or_create(name='astrobin_ultimate_2020')

Group.objects.get_or_create(name='astrobin-donor-bronze-monthly')
Group.objects.get_or_create(name='astrobin-donor-silver-monthly')
Group.objects.get_or_create(name='astrobin-donor-gold-monthly')
Group.objects.get_or_create(name='astrobin-donor-platinum-monthly')

Group.objects.get_or_create(name='astrobin-donor-bronze-yearly')
Group.objects.get_or_create(name='astrobin-donor-silver-yearly')
Group.objects.get_or_create(name='astrobin-donor-gold-yearly')
Group.objects.get_or_create(name='astrobin-donor-platinum-yearly')

cookies = [
    [
        'essential',
        'Essential cookies',
        'These cookies are essential for the website to function properly.',
        [
            ['astrobin_cookie_consent', 'This cookie is used to store your cookie preferences.'],
            ['sessionid', 'This cookie is used to identify your session on the website.'],
            ['csrftoken', 'This cookie is used to protect against Cross-Site Request Forgery (CSRF) attacks.'],
            ['astrobin_lang', 'This cookie is used to remember your language preference.'],
            ['multidb_pin_writes', 'This cookie is used to pin your session to the master database: AstroBin uses multiple databases to improve performance, and this cookie is used to make sure that all your requests are sent to the same database.'],
            ['classic-auth-token', 'This cookie is used to authenticate you on the website app.astrobin.com.'],
            ['__stripe_mid', 'This cookie is set by Stripe and used for fraud prevention. It is only set is you purchase a subscription'],
            ['__stripe_sid', 'This cookie is set by Stripe and used for fraud prevention. It is only set is you purchase a subscription'],
        ]
    ],
    [
        'functional',
        'Functional cookies (recommended)',
        'These cookies are used to provide additional functionality to the website, such as remembering local preferences.',
        [
            ['astrobin_forum_usage_modal_seen', 'This cookie is used to remember if you have seen the information about proper usage of the forums.'],
            ['astrobin_click_and_drag_toast_seen', 'This cookie is used to remember if you have seen information about the click & drag zoom functionality.'],
            ['astrobin_use_high_contrast_theme', 'This cookie is used to remember if you have enabled the high contrast theme.'],
        ]
    ],
    [
        'performance',
        'Performance cookies (recommended)',
        'These cookies are used to improve the website performance by saving some pieces of information on your computer and avoiding reading from the AstroBin database when possible.',
        [
            ['astrobin_last_seen_set', 'This cookie is used avoid saving the date and time we last saw you too often.'],
        ]
    ],
    [
        'analytics',
        'Analytics cookies',
        'These cookies are used to anonymously track your usage of the website, so that we can improve it over time.',
        [
            ['_ga', 'This cookie is used by Google Analytics to anonymously track your usage of the website.'],
            ['_gid', 'This cookie is used by Google Analytics to anonymously track your usage of the website.'],
            ['_gat', 'This cookie is used by Google Analytics to anonymously track your usage of the website.'],
            [f'_gac_{settings.GOOGLE_ANALYTICS_ID}', 'This cookie is used by Google Analytics to anonymously track your usage of the website.'],
            ['_hjClosedSurveyInvites', 'This cookie is set once a visitor interacts with a Survey invitation modal popup. It is used to ensure that the same invite does not reappear if it has already been shown.'],
            ['_hjDonePolls', 'This cookie is set once a visitor completes a poll using the Feedback Poll widget. It is used to ensure that the same poll does not reappear if it has already been filled in.'],
            ['_hjMinimizedPolls', 'This cookie is set once a visitor minimizes a Feedback Poll widget. It is used to ensure that the widget stays minimized when the visitor navigates through your site.'],
            ['_hjDoneTestersWidgets', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjMinimizedTestersWidgets', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjIncludedInSample', 'This session cookie is set to let Hotjar know whether that visitor is included in the sample which is used to generate funnels.'],
            ['_hjShownFeedbackMessage', 'This cookie is set when a visitor minimizes or completes Incoming Feedback. This is done so that the Incoming Feedback will load as minimized immediately if the visitor navigates to another page where it is set to show.'],
            ['_hjid', 'This cookie is set when the customer first lands on a page with the Hotjar script. It is used to persist the Hotjar User ID, unique to that site on the browser. This ensures that behavior in subsequent visits to the same site will be attributed to the same user ID.'],
            ['_hjRecordingLastActivity', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjTLDTest', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjUserAttributesHash', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjCachedUserAttributes', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjLocalStorageTest', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjIncludedInPageviewSample', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjAbsoluteSessionInProgress', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjFirstSeen', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjViewportId', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjRecordingEnabled', 'This cookie is used by Hotjar to anonymously track your usage of the website.'],
            ['_hjRecordingLastActivity', 'This cookie is used by Hotjar to anonymously track your usage of the website'],
        ]
    ],
    [
        'advertising',
        'Advertising cookies',
        'These cookies are used to honor ad display frequency caps. AstroBin does NOT serve targeted ads.',
        [
            ['IDE', 'This cookie is used by Google Ad Manager to register and report the website user\'s actions after viewing or clicking one of the advertiser\'s ads with the purpose of measuring the efficacy of an ad.'],
            ['test_cookie', 'This cookie is used by Google Ad Manager to check if the user\'s browser supports cookies.'],
        ]
    ],
]

for index, group in enumerate(cookies):
    cookie_group = CookieGroup.objects.get_or_create(
        varname=group[0],
        name=group[1],
        description=group[2],
        is_required=group[0] == 'essential',
        ordering=index,
    )[0]

    for cookie in group[3]:
        Cookie.objects.get_or_create(
            cookiegroup=cookie_group,
            name=cookie[0],
            description=cookie[1],
        )

try:
    Subscription.objects.get(name=SubscriptionName.LITE_CLASSIC.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.LITE_CLASSIC.value,
        currency="USD",
        price=18,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_lite'),
        category='premium')

try:
    Subscription.objects.get(name=SubscriptionName.LITE_CLASSIC.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.LITE_CLASSIC.value,
        currency="USD",
        price=18,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='Y',
        group=Group.objects.get(name='astrobin_lite'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name=SubscriptionName.LITE_2020.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.LITE_2020.value,
        currency="CHF",
        price=20,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_lite_2020'),
        category='premium')

try:
    Subscription.objects.get(name=SubscriptionName.LITE_2020_AUTORENEW_MONTHLY.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.LITE_2020_AUTORENEW_MONTHLY.value,
        currency="CHF",
        price=2.5,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='M',
        group=Group.objects.get(name='astrobin_lite_2020'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name=SubscriptionName.LITE_2020_AUTORENEW_YEARLY.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.LITE_2020_AUTORENEW_YEARLY.value,
        currency="CHF",
        price=20,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='Y',
        group=Group.objects.get(name='astrobin_lite_2020'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name=SubscriptionName.PREMIUM_CLASSIC.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.PREMIUM_CLASSIC.value,
        currency="USD",
        price=36,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_premium'),
        category='premium')

try:
    Subscription.objects.get(name=SubscriptionName.PREMIUM_CLASSIC_AUTORENEW.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.PREMIUM_CLASSIC_AUTORENEW.value,
        currency="USD",
        price=36,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='Y',
        group=Group.objects.get(name='astrobin_premium'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name=SubscriptionName.PREMIUM_2020.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.PREMIUM_2020.value,
        currency="CHF",
        price=40,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_premium_2020'),
        category='premium')

try:
    Subscription.objects.get(name=SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY.value,
        currency="CHF",
        price=4.5,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='M',
        group=Group.objects.get(name='astrobin_premium_2020'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name=SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY.value,
        currency="CHF",
        price=40,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='Y',
        group=Group.objects.get(name='astrobin_premium_2020'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name=SubscriptionName.ULTIMATE_2020.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.ULTIMATE_2020.value,
        currency="CHF",
        price=60,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_ultimate_2020'),
        category='premium')

try:
    Subscription.objects.get(name=SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY.value,
        currency="CHF",
        price=6.5,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='M',
        group=Group.objects.get(name='astrobin_ultimate_2020'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name=SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY.value)
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name=SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY.value,
        currency="CHF",
        price=60,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='Y',
        group=Group.objects.get(name='astrobin_ultimate_2020'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name='AstroBin Donor Bronze Monthly')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Donor Bronze Monthly',
        currency="CHF",
        price=2.50,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit="M",
        group=Group.objects.get(name='astrobin-donor-bronze-monthly'),
        category='donor')

try:
    Subscription.objects.get(name='AstroBin Donor Silver Monthly')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Donor Silver Monthly',
        currency="CHF",
        price=5,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit="M",
        group=Group.objects.get(name='astrobin-donor-silver-monthly'),
        category='donor')

try:
    Subscription.objects.get(name='AstroBin Donor Gold Monthly')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Donor Gold Monthly',
        currency="CHF",
        price=10,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit="M",
        group=Group.objects.get(name='astrobin-donor-gold-monthly'),
        category='donor')

try:
    Subscription.objects.get(name='AstroBin Donor Platinum Monthly')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Donor Platinum Monthly',
        currency="CHF",
        price=20,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit="M",
        group=Group.objects.get(name='astrobin-donor-platinum-monthly'),
        category='donor')

try:
    Subscription.objects.get(name='AstroBin Donor Bronze Yearly')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Donor Bronze Yearly',
        currency="CHF",
        price=27.50,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit="Y",
        group=Group.objects.get(name='astrobin-donor-bronze-yearly'),
        category='donor')

try:
    Subscription.objects.get(name='AstroBin Donor Silver Yearly')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Donor Silver Yearly',
        currency="CHF",
        price=55,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit="Y",
        group=Group.objects.get(name='astrobin-donor-silver-yearly'),
        category='donor')

try:
    Subscription.objects.get(name='AstroBin Donor Gold Yearly')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Donor Gold Yearly',
        currency="CHF",
        price=110,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit="Y",
        group=Group.objects.get(name='astrobin-donor-gold-yearly'),
        category='donor')

try:
    Subscription.objects.get(name='AstroBin Donor Platinum Yearly')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Donor Platinum Yearly',
        currency="CHF",
        price=220,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit="Y",
        group=Group.objects.get(name='astrobin-donor-platinum-yearly'),
        category='donor')

Group.objects.get_or_create(name='auto_approve_content')
Group.objects.get_or_create(name='content_moderators')
Group.objects.get_or_create(name='image_moderators')
Group.objects.get_or_create(name=GroupName.OWN_EQUIPMENT_MIGRATORS)
Group.objects.get_or_create(name=GroupName.GLOBAL_EQUIPMENT_MIGRATORS)
Group.objects.get_or_create(name=GroupName.EQUIPMENT_MODERATORS)
Group.objects.get_or_create(name='iotd_staff')
Group.objects.get_or_create(name='iotd_submitters')
Group.objects.get_or_create(name='iotd_reviewers')
Group.objects.get_or_create(name='iotd_judges')

try:
    User.objects.get(username='astrobin')
except User.DoesNotExist:
    u = User.objects.create_superuser('astrobin', 'astrobin@astrobin.com', 'astrobin')
    Group.objects.get(name='content_moderators').user_set.add(u)
    Group.objects.get(name='image_moderators').user_set.add(u)

try:
    User.objects.get(username='astrobin_dev')
except User.DoesNotExist:
    u = User.objects.create_superuser('astrobin_dev', 'dev@astrobin.com', 'astrobin_dev')
    Group.objects.get(name='content_moderators').user_set.add(u)
    Group.objects.get(name='image_moderators').user_set.add(u)

try:
    User.objects.get(username='astrobin_dev2')
except User.DoesNotExist:
    u = User.objects.create_superuser('astrobin_dev2', 'dev2@astrobin.com', 'astrobin_dev2')
    Group.objects.get(name='content_moderators').user_set.add(u)
    Group.objects.get(name='image_moderators').user_set.add(u)

category, created = Category.objects.get_or_create(name="AstroBin Meta Forums", slug="astrobin")
Forum.objects.get_or_create(category=category, name="Announcements", slug="announcements")

try:
    Site.objects.get(name="AstroBin")
except Site.DoesNotExist:
    Site.objects.create(name='AstroBin', domain='localhost')
EOF
