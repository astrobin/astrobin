#!/bin/sh

# Migrate
python manage.py migrate --noinput
python manage.py migrate --run-syncdb --noinput
python manage.py sync_translation_fields --noinput

# Create initial data

# Create Premium groups
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='astrobin_lite')" | python manage.py shell
echo "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='astrobin_premium')" | python manage.py shell

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
