#!/bin/sh

# Migrate
python manage.py migrate --noinput
python manage.py migrate --run-syncdb --noinput
python manage.py sync_translation_fields --noinput

# Create Premium subsciptions
python manage.py shell << EOF
from subscription.models import Subscription
from django.contrib.auth.models import Group

Group.objects.get_or_create(name='astrobin_lite')
Group.objects.get_or_create(name='astrobin_lite_2020')
Group.objects.get_or_create(name='astrobin_premium')
Group.objects.get_or_create(name='astrobin_premium_2020')
Group.objects.get_or_create(name='astrobin_ultimate_2020')

Group.objects.get_or_create(name='rawdata-meteor-2020')
Group.objects.get_or_create(name='rawdata-luna-2020')
Group.objects.get_or_create(name='rawdata-sol-2020')

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
        category='premium')

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
        category='premium')

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
    Subscription.objects.get(name='AstroBin Raw Data Meteor 2020+')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Raw Data Meteor 2020+',
        description="50 GB",
        currency="CHF",
        price=3,
        trial_period=7,
        trial_unit="D",
        recurrence_period=1,
        recurrence_unit="M",
        group=Group.objects.get(name='rawdata-meteor-2020'),
        category='rawdata')

try:
    Subscription.objects.get(name='AstroBin Raw Data Luna 2020+')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Raw Data Luna 2020+',
        description="250 GB",
        currency="CHF",
        price=15,
        trial_period=7,
        trial_unit="D",
        recurrence_period=1,
        recurrence_unit="M",
        group=Group.objects.get(name='rawdata-luna-2020'),
        category='rawdata')

try:
    Subscription.objects.get(name='AstroBin Raw Data Sol 2020+')
except Subscription.DoesNotExist:
    Subscription.objects.get_or_create(
        name='AstroBin Raw Data Sol 2020+',
        description="500 GB",
        currency="CHF",
        price=30,
        trial_period=7,
        trial_unit="D",
        recurrence_period=1,
        recurrence_unit="M",
        group=Group.objects.get(name='rawdata-sol-2020'),
        category='rawdata')

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
EOF

# Create moderation groups
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='content_moderators')" | python manage.py shell
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='image_moderators')" | python manage.py shell

# Create Raw Data groups
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='rawdata-atom')" | python manage.py shell

# Create IOTD board groups
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='iotd_staff')" | python manage.py shell
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='iotd_submitters')" | python manage.py shell
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='iotd_reviewers')" | python manage.py shell
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='iotd_judges')" | python manage.py shell

# Create superuser
echo "from django.contrib.auth.models import User; User.objects.filter(email='dev@astrobin.com').delete(); User.objects.create_superuser('astrobin_dev', 'dev@astrobin.com', 'astrobin_dev')" | python manage.py shell

# Assign superuser to some groups
echo "from django.contrib.auth.models import User, Group; u = User.objects.get(username='astrobin_dev'); g = Group.objects.get(name='content_moderators'); g.user_set.add(u)" | python manage.py shell
echo "from django.contrib.auth.models import User, Group; u = User.objects.get(username='astrobin_dev'); g = Group.objects.get(name='image_moderators'); g.user_set.add(u)" | python manage.py shell

# Create Site
echo "from django.contrib.sites.models import Site; Site.objects.get_or_create(name='AstroBin', domain='localhost')" | python manage.py shell
