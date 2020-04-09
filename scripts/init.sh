#!/bin/sh

# Migrate
python manage.py migrate --noinput
python manage.py migrate --run-syncdb --noinput
python manage.py sync_translation_fields --noinput

# Create initial data
python manage.py shell << EOF
from subscription.models import Subscription
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site

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

try:
    Subscription.objects.get(name='AstroBin Lite')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Lite',
        currency="USD",
        price=18,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_lite'),
        category='premium')

try:
    Subscription.objects.get(name='AstroBin Lite (autorenew)')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Lite (autorenew)',
        currency="USD",
        price=18,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='Y',
        group=Group.objects.get(name='astrobin_lite'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name='AstroBin Lite 2020+')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Lite 2020+',
        currency="CHF",
        price=20,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_lite_2020'),
        category='premium')

try:
    Subscription.objects.get(name='AstroBin Premium')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Premium',
        currency="USD",
        price=36,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_premium'),
        category='premium')

try:
    Subscription.objects.get(name='AstroBin Premium (autorenew)')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Premium (autorenew)',
        currency="USD",
        price=36,
        trial_period=0,
        trial_unit=None,
        recurrence_period=1,
        recurrence_unit='Y',
        group=Group.objects.get(name='astrobin_premium'),
        category='premium_autorenew')

try:
    Subscription.objects.get(name='AstroBin Premium 2020+')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Premium 2020+',
        currency="CHF",
        price=40,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_premium_2020'),
        category='premium')

try:
    Subscription.objects.get(name='AstroBin Ultimate 2020+')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Ultimate 2020+',
        currency="CHF",
        price=60,
        trial_period=0,
        trial_unit=None,
        recurrence_period=0,
        recurrence_unit=None,
        group=Group.objects.get(name='astrobin_ultimate_2020'),
        category='premium')

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

Group.objects.get_or_create(name='content_moderators')
Group.objects.get_or_create(name='image_moderators')
Group.objects.get_or_create(name='iotd_staff')
Group.objects.get_or_create(name='iotd_submitters')
Group.objects.get_or_create(name='iotd_reviewers')
Group.objects.get_or_create(name='iotd_judges')

try:
    User.objects.get(email='dev@astrobin.com')
except User.DoesNotExist:
    u = User.objects.create_superuser('astrobin_dev', 'dev@astrobin.com', 'astrobin_dev')
    Group.objects.get(name='content_moderators').user_set.add(u)
    Group.objects.get(name='image_moderators').user_set.add(u)

try:
    Site.objects.get(name="AstroBin")
except Site.DoesNotExist:
    Site.objects.create(name='AstroBin', domain='localhost')
EOF
