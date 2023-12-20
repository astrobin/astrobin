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

from astrobin.types import CookieGroupDefinition, CookieGroupName, CookieGroupDescription, cookie_definitions
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
        CookieGroupDefinition.ESSENTIAL.value,
        CookieGroupName.ESSENTIAL.value,
        CookieGroupDescription.ESSENTIAL.value,
        [
            'astrobin_cookie_consent',
            'sessionid',
            'csrftoken',
            'astrobin_lang',
            'astrobin-two-factor-remember-cookie',
            'astrobin-equipment-explorer-filter-data-camera',
            'astrobin-equipment-explorer-filter-data-sensor',
            'astrobin-equipment-explorer-filter-data-telescope',
            'astrobin-equipment-explorer-filter-data-mount',
            'astrobin-equipment-explorer-filter-data-filter',
            'astrobin-equipment-explorer-filter-data-software',
            'astrobin-equipment-explorer-filter-data-accessory',
            'multidb_pin_writes',
            'classic-auth-token',
            '__stripe_mid',
            '__stripe_sid',
        ]
    ],
    [
        CookieGroupDefinition.FUNCTIONAL.value,
        CookieGroupName.FUNCTIONAL.value,
        CookieGroupDescription.FUNCTIONAL.value,
        [
            'astrobin_forum_usage_modal_seen',
            'astrobin_click_and_drag_toast_seen',
            'astrobin_use_high_contrast_theme',
        ]
    ],
    [
        CookieGroupDefinition.PERFORMANCE.value,
        CookieGroupName.PERFORMANCE.value,
        CookieGroupDescription.PERFORMANCE.value,
        [
            'astrobin_last_seen_set',
        ]
    ],
    [
        CookieGroupDefinition.ANALYTICS.value,
        CookieGroupName.ANALYTICS.value,
        CookieGroupDescription.ANALYTICS.value,
        [
            '_ga',
            '_gid',
            '_gat',
            f'_gac_{settings.GOOGLE_ANALYTICS_ID}',
        ]
    ],
    [
        CookieGroupDefinition.ADVERTISING.value,
        CookieGroupName.ADVERTISING.value,
        CookieGroupDescription.ADVERTISING.value,
        [
            'IDE',
            'test_cookie',
        ]
    ],
]

for index, group in enumerate(cookies):
    cookie_group = CookieGroup.objects.get_or_create(
        varname=group[0],
        name=group[1],
        description=group[2],
        is_required=group[0] == CookieGroupDefinition.ESSENTIAL.value,
        ordering=index,
    )[0]

    for cookie in group[3]:
        Cookie.objects.get_or_create(
            cookiegroup=cookie_group,
            name=cookie,
            description=cookie_definitions[cookie],
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
Group.objects.get_or_create(name=GroupName.IOTD_STAFF)
Group.objects.get_or_create(name=GroupName.IOTD_SUBMITTERS)
Group.objects.get_or_create(name=GroupName.IOTD_REVIEWERS)
Group.objects.get_or_create(name=GroupName.IOTD_JUDGES)

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
