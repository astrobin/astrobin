#!/bin/sh

# Collect static files
python manage.py collectstatic --noinput

# Migrate
python manage.py migrate --noinput
python manage.py migrate --run-syncdb --noinput

# Create initial data
python manage.py shell << EOF
from common.constants import GroupName
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

essential_cookies_group = CookieGroup.objects.get_or_create(
    varname='essential',
    name='Essential cookies',
    description='These cookies are essential for the website to function properly.',
    is_required=True,
    ordering=0,
)[0]

astrobin_cookie_consent_cookie = Cookie.objects.get_or_create(
    cookiegroup=essential_cookies_group,
    name='astrobin_cookie_consent',
    description='This cookie is used to store your cookie preferences.',
)[0]

sessionid_cookie = Cookie.objects.get_or_create(
    cookiegroup=essential_cookies_group,
    name='sessionid',
    description='This cookie is used to identify your session on the website.',
)[0]

csrftoken_cookie = Cookie.objects.get_or_create(
    cookiegroup=essential_cookies_group,
    name='csrftoken',
    description='This cookie is used to protect against Cross-Site Request Forgery (CSRF) attacks.',
)[0]

astrobin_lang_cookie = Cookie.objects.get_or_create(
    cookiegroup=essential_cookies_group,
    name='astrobin_lang',
    description='This cookie is used to remember your language preference.',
)[0]

multidb_pin_writes_cookie = Cookie.objects.get_or_create(
    cookiegroup=essential_cookies_group,
    name='multidb_pin_writes',
    description='This cookie is used to pin your session to the master database: AstroBin uses multiple databases ' +
        'to improve performance, and this cookie is used to make sure that all your requests are sent to ' +
        'the same database.',
)[0]

classic_auth_token_cookie = Cookie.objects.get_or_create(
    cookiegroup=essential_cookies_group,
    name='classic-auth-token',
    description='This cookie is used to authenticate you on the website app.astrobin.com.',
)[0]

__stripe_mid_cookie = Cookie.objects.get_or_create(
    cookiegroup=essential_cookies_group,
    name='__stripe_mid',
    description='This cookie is set by Stripe and used for fraud prevention. It is only set is you purchase a subscription',
)[0]

__stripe_sid_cookie = Cookie.objects.get_or_create(
    cookiegroup=essential_cookies_group,
    name='__stripe_sid',
    description='This cookie is set by Stripe and used for fraud prevention. It is only set is you purchase a subscription',
)[0]

functional_cookies_group = CookieGroup.objects.get_or_create(
    varname='functional',
    name='Functional cookies (recommended)',
    description='These cookies are used to provide additional functionality to the website, ' +
        'such as remembering local preferences.',
    is_required=False,
    ordering=1,
)[0]

astrobin_forum_usage_modal_seen_cookie = Cookie.objects.get_or_create(
    cookiegroup=functional_cookies_group,
    name='astrobin_forum_usage_modal_seen',
    description='This cookie is used to remember if you have seen the information about proper usage of the forums.',
)[0]

astrobin_click_and_drag_toast_seen = Cookie.objects.get_or_create(
    cookiegroup=functional_cookies_group,
    name='astrobin_click_and_drag_toast_seen',
    description='This cookie is used to remember if you have seen information about the click & drag zoom ' +
        'functionality.',
)[0]

astrobin_use_high_contrast_theme_cookie = Cookie.objects.get_or_create(
    cookiegroup=functional_cookies_group,
    name='astrobin_use_high_contrast_theme',
    description='This cookie is used to remember if you have enabled the high contrast theme.',
)[0]

performance_cookies_group = CookieGroup.objects.get_or_create(
    varname='performance',
    name='Performance cookies (recommended)',
    description='These cookies are used to improve the website performance by saving some ' +
        'pieces of information on your computer and avoiding reading from the ' +
        'AstroBin database when possible.',
    is_required=False,
    ordering=2
)[0]

astrobin_last_seen_set_cookie = Cookie.objects.get_or_create(
    cookiegroup=performance_cookies_group,
    name='astrobin_last_seen_set',
    description='This cookie is used avoid saving the date and time we last saw you too often.',
)[0]

analytics_cookies_group = CookieGroup.objects.get_or_create(
    varname='analytics',
    name='Analytics cookies',
    description='These cookies are used to anonymously track your usage of the website, so that we can ' +
        'improve it over time.',
    is_required=False,
    ordering=3
)[0]

advertising_cookies_group = CookieGroup.objects.get_or_create(
    varname='advertising',
    name='Advertising cookies',
    description='These cookies are used to honor ad display frequency caps. AstroBin does NOT serve targeted ads.',
    is_required=False,
    ordering=4
)[0]

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
