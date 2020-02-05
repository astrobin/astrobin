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
