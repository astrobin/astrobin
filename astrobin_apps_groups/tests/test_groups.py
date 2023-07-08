import re

import simplejson as json
from bs4 import BeautifulSoup as BS
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from pybb.models import Forum, Topic

from astrobin.models import Image
from astrobin.tests.generators import Generators
from astrobin_apps_groups.models import Group, GroupCategory, GroupImageSorting
from astrobin_apps_premium.services.premium_service import SubscriptionName
from toggleproperties.models import ToggleProperty


class GroupsTest(TestCase):
    def _assertMessage(self, response, tags, content):
        messages = response.context[0]['messages']

        if len(messages) == 0:
            self.assertEqual(False, True)

        found = False
        for message in messages:
            if message.tags == tags and message.message == content:
                found = True

        self.assertEqual(found, True)

    def setUp(self):
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'password')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'password')
        self.group = Group.objects.create(
            creator=self.user1,
            owner=self.user1,
            name='Test group',
            category=101,
            public=True,
            moderated=False,
            autosubmission=True
        )

    def test_misc_ui_elements(self):
        response = self.client.get(reverse('group_list'))
        bs = BS(response.content, 'lxml')
        self.assertEqual(len(bs.select('.explore-menu-groups')), 1)

    def test_group_list_view(self):
        response = self.client.get(reverse('group_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<td class="group-name"><a href="' + reverse('group_detail', args=(
            self.group.pk, self.group.slug)) + '">Test group</a></td>', html=True)
        self.assertContains(response, '<td class="group-members hidden-phone">1</td>', html=True)
        self.assertContains(response, '<td class="group-images hidden-phone">0</td>', html=True)

        # Add a member
        self.group.members.add(self.user2)
        response = self.client.get(reverse('group_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<td class="group-members hidden-phone">2</td>', html=True)
        self.assertContains(response, '<td class="group-images hidden-phone">0</td>', html=True)

        # Add an image for the one member
        image = Image.objects.create(title='Test image', user=self.user2)
        response = self.client.get(reverse('group_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<td class="group-members hidden-phone">2</td>', html=True)
        self.assertContains(response, '<td class="group-images hidden-phone">1</td>', html=True)

        # Test that WIP images don't work
        image.is_wip = True
        image.save(keep_deleted=True)
        response = self.client.get(reverse('group_list'))
        self.assertContains(response, '<td class="group-images hidden-phone">0</td>', html=True)

        # Private groups that do not pertain this user are not visible here
        self.group.public = False
        self.group.save()
        response = self.client.get(reverse('group_list'))
        self.assertNotContains(response, 'Test group')

    def test_group_detail_view(self):
        # Everything okay when it's empty
        response = self.client.get(reverse('group_detail', kwargs={'pk': self.group.pk, 'slug': self.group.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li>No images.</li>', html=True)

        # Test that images are rendered and members can access
        self.client.login(username='user1', password='password')
        self.client.post(
            reverse('image_upload_process'),
            {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
            follow=True)
        self.client.logout()
        image = Image.objects.all().order_by('-pk')[0]
        self.group.members.add(self.user1)
        response = self.client.get(reverse('group_detail', kwargs={'pk': self.group.pk, 'slug': self.group.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-id-or-hash="%s"\s+data-alias="%s"' % (image.pk, image.get_id(), "gallery"), response.content.decode(
            'utf-8')))

        # Test that WIP images are not rendered here
        image.is_wip = True
        image.save(keep_deleted=True)
        response = self.client.get(reverse('group_detail', kwargs={'pk': self.group.pk, 'slug': self.group.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li>No images.</li>', html=True)

        # Test that the group is not accessible if it's private
        self.group.public = False
        self.group.save()
        response = self.client.get(reverse('group_detail', kwargs={'pk': self.group.pk, 'slug': self.group.slug}))
        self.assertEqual(response.status_code, 403)

        # However, invitees can access
        self.client.login(username='user2', password='password')
        self.group.members.remove(self.user1)
        self.group.invited_users.add(self.user2)
        response = self.client.get(reverse('group_detail', kwargs={'pk': self.group.pk, 'slug': self.group.slug}))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_group_create_view(self):
        url = reverse('group_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Add user2 to user1's followers to check notification
        ToggleProperty.objects.create_toggleproperty("follow", self.user1, self.user2)

        # Free users can't access.
        self.client.login(username='user1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        Generators.premium_subscription(self.user1, SubscriptionName.ULTIMATE_2020)

        self.client.login(username='user1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {
            'name': 'Test create group',
            'description': 'Description',
            'category': GroupCategory.OTHER,
            'default_image_sorting': GroupImageSorting.PUBLICATION,
            'public': True,
            'moderated': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "success unread", "Your new group was created successfully")
        group = Group.objects.all().order_by('-pk')[0]
        self.assertEqual(group.creator, self.user1)
        self.assertEqual(group.owner, self.user1)
        self.assertEqual(group.name, 'Test create group')
        self.assertEqual(group.description, 'Description')
        self.assertEqual(group.category, GroupCategory.OTHER)
        self.assertEqual(group.public, True)
        self.assertEqual(group.moderated, True)
        self.assertTrue(group.owner in group.members.all())
        self.assertTrue(group.owner in group.moderators.all())
        self.assertIsNotNone(group.forum)
        group.delete()

        # Creating a private group does not trigger notifications
        response = self.client.post(url, {
            'name': 'Test create group',
            'description': 'Description',
            'category': GroupCategory.OTHER,
            'default_image_sorting': GroupImageSorting.PUBLICATION,
            'public': False,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "success unread", "Your new group was created successfully")
        group = Group.objects.all().order_by('-pk')[0]
        self.assertEqual(group.public, False)
        group.delete()

        # Test the autosubmission/category combo
        response = self.client.post(url, {
            'name': 'Test create group',
            'description': 'Description',
            'category': GroupCategory.OTHER,
            'default_image_sorting': GroupImageSorting.PUBLICATION,
            'autosubmission': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Only the following category support autosubmission:')

    def test_group_update_view(self):
        url = reverse('group_update', kwargs={'pk': self.group.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='user2', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        self.client.login(username='user1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Upload an image
        self.client.post(
            reverse('image_upload_process'),
            {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
            follow=True)
        self.assertEqual(self.group.images.count(), 1)

        response = self.client.post(url, {
            'name': 'Updated group name',
            'description': 'Updated group description',
            'category': GroupCategory.PROFESSIONAL_NETWORK,
            'default_image_sorting': GroupImageSorting.PUBLICATION,
            'public': False,
            'moderated': True,
            'autosubmission': False,
            'autosubmission_deactivation_strategy': 'delete',
        }, follow=True)
        self._assertMessage(response, "success unread", "Form saved")
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group.name, 'Updated group name')
        self.assertEqual(self.group.description, 'Updated group description')
        self.assertEqual(self.group.category, GroupCategory.PROFESSIONAL_NETWORK)
        self.assertEqual(self.group.public, False)
        self.assertEqual(self.group.moderated, True)
        self.assertEqual(self.group.forum.name, self.group.name)
        self.assertEqual(self.group.images.count(), 0)

    def test_group_delete_view(self):
        group = Group.objects.create(
            creator=self.user1,
            owner=self.user1,
            name='Delete me',
            category=101,
            public=True,
            moderated=False,
            autosubmission=True
        )

        url = reverse('group_delete', kwargs={'pk': group.pk})

        # Login required
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # Owner required
        self.client.login(username='user2', password='password')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Login the owner now
        self.client.login(username='user1', password='password')

        # Group does not exist
        response = self.client.post(reverse('group_delete', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Success
        self.assertEqual(Forum.objects.filter(category__slug='group-forums', name='Delete me').count(), 1)
        response = self.client.post(url)
        self.assertRedirects(response, reverse('group_list'))
        self.assertEqual(Group.objects.filter(name='Delete me').count(), 0)
        self.assertEqual(Forum.objects.filter(category__slug='group-forums', name='Delete me').count(), 0)

    def test_group_join_view(self):
        url = reverse('group_join', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='user1', password='password')

        # Free users can access.
        self.client.login(username='user1', password='password')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 403)

        Generators.premium_subscription(self.user1, SubscriptionName.ULTIMATE_2020)

        # GET not allowed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Group does not exist
        response = self.client.post(reverse('group_join', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        self.client.logout()
        self.client.login(username='user2', password='password')

        Generators.premium_subscription(self.user2, SubscriptionName.ULTIMATE_2020)

        # Private group, uninvited user
        self.group.public = False
        self.group.save()
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.group.public = True
        self.group.save()

        # Public group, but moderated
        self.group.moderated = True
        self.group.save()
        self.group.moderators.add(self.group.owner)
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "warning unread",
                            "This is a moderated group, and your join request will be reviewed by a moderator")
        self.assertTrue(self.user2 in self.group.join_requests.all())
        self.group.moderated = False
        self.group.save()
        self.group.moderators.clear()

        # Join successful
        ToggleProperty.objects.create_toggleproperty("follow", self.user2, self.user1)
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "success unread", "You have joined the group")
        self.assertTrue(self.user2 in self.group.members.all())

        # Second attempt results in error "already joined"
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "error unread", "You already were a member of this group")
        self.group.members.remove(self.user2)

        # If the group is not public, only invited members can join
        self.group.public = False
        self.group.save()
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)

        self.group.invited_users.add(self.user2)
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "success unread", "You have joined the group")
        self.assertTrue(self.user2 in self.group.members.all())
        self.assertFalse(self.user2 in self.group.invited_users.all())

    def test_group_leave_view(self):
        url = reverse('group_leave', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='user1', password='password')
        self.group.members.add(self.user1)

        # GET not allowed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Group does not exist
        response = self.client.post(reverse('group_leave', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Upload an image
        self.client.post(
            reverse('image_upload_process'),
            {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
            follow=True)
        image = Image.objects.all().order_by('-pk')[0]

        # Private group
        self.group.public = False
        self.group.save()
        response = self.client.post(url, follow=True)
        self.assertFalse(self.user1 in self.group.members.all())
        self.assertFalse(image in self.group.images.all())
        self.assertRedirects(response, reverse('group_list'))
        self._assertMessage(response, "success unread", "You have left the group")
        self.group.public = True
        self.group.save()
        self.group.members.add(self.user1)

        # Public group
        response = self.client.post(url, follow=True)
        self.assertFalse(self.user1 in self.group.members.all())
        self.assertFalse(image in self.group.images.all())
        self.assertRedirects(response, reverse('group_detail', kwargs={'pk': self.group.pk, 'slug': self.group.slug}))
        self._assertMessage(response, "success unread", "You have left the group")
        self.group.members.add(self.user1)

        # Try with non-autosub group, to test for image removal
        self.group.autosubmission = False
        self.group.save()
        self.group.images.add(image)
        response = self.client.post(url, follow=True)
        self.assertFalse(self.user1 in self.group.members.all())
        self.assertFalse(image in self.group.images.all())
        self.group.autosubmission = True
        self.group.save()

        # Second attempt results in error 403
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)

        # All forum topics should be unsubscribed, but only if the group is private
        self.group.members.add(self.user1)
        topic = Topic.objects.create(forum=self.group.forum, name='Test', user=self.user1)
        topic.subscribers.add(self.user1)
        response = self.client.post(url, follow=True)
        self.assertTrue(self.user1 in topic.subscribers.all())
        topic.delete()

        self.group.public = False
        self.group.save()
        self.group.members.add(self.user1)
        topic = Topic.objects.create(forum=self.group.forum, name='Test', user=self.user1)
        topic.subscribers.add(self.user1)
        self.client.post(url, follow=True)
        self.assertFalse(self.user1 in topic.subscribers.all())

    def test_group_invite_view(self):
        url = reverse('group_invite', kwargs={'pk': self.group.pk})
        detail_url = reverse('group_detail', kwargs={'pk': self.group.pk, 'slug': self.group.slug})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Owner required
        self.client.login(username='user2', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        self.client.login(username='user1', password='password')

        # GET not allowed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Group does not exist
        response = self.client.post(reverse('group_invite', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Invited user does not exist
        response = self.client.post(
            url,
            {
                'users[]': [999],
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertEqual(self.group.invited_users.count(), 0)

        # Invitation successful
        response = self.client.post(
            url,
            {
                'users[]': [self.user2.pk, ],
            }
        )
        self.assertRedirects(response, detail_url, status_code=302, target_status_code=200)
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertEqual(self.group.invited_users.count(), 1)
        self.group.invited_users.clear()

        # AJAX invitation successful
        response = self.client.post(
            url,
            {
                'users[]': [self.user2.pk, ],
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.group = Group.objects.get(pk=self.group.pk)
        self.assertEqual(json.loads(response.content)['invited_users'][0]['id'], self.user2.pk)
        self.assertEqual(self.group.invited_users.count(), 1)

    def test_group_revoke_invitation_view(self):
        url = reverse('group_revoke_invitation', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Owner required
        self.client.login(username='user2', password='password')
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        self.client.login(username='user1', password='password')

        # GET not allowed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Group does not exist
        response = self.client.post(reverse('group_revoke_invitation', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # User does not exist
        response = self.client.post(
            url,
            {
                'user': "invalid",
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 404)

        # Success
        self.group.invited_users.add(self.user2)
        response = self.client.post(
            url,
            {
                'user': "user2",
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group.invited_users.count(), 0)

    def test_group_add_remove_images_view(self):
        url = reverse('group_add_remove_images', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='user1', password='password')

        # Member required
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)

        self.group.members.add(self.user1)

        # Group does not exist
        response = self.client.post(reverse('group_add_remove_images', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Upload an image
        self.client.post(
            reverse('image_upload_process'),
            {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
            follow=True)
        image = Image.objects.all().order_by('-pk')[0]

        # Upload another
        self.client.post(
            reverse('image_upload_process'),
            {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
            follow=True)
        image2 = Image.objects.all().order_by('-pk')[0]

        # Cannot add/remove on autosubmission groups
        response = self.client.post(
            url,
            {
                'images[]': "%d" % image.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 403)

        self.group.autosubmission = False
        self.group.save()

        # Successfully add
        self.group.members.add(self.user2)
        response = self.client.post(
            url,
            {
                'images[]': [image.pk, image2.pk],
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group.images.count(), 2)
        self.group.members.remove(self.user2)

        # Successfully remove
        response = self.client.post(
            url,
            {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group.images.count(), 0)

    def test_group_add_image_view(self):
        url = reverse('group_add_image', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='user1', password='password')

        # Member required
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)

        self.group.members.add(self.user1)

        # Group does not exist
        response = self.client.post(reverse('group_add_image', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Upload an image
        self.client.post(
            reverse('image_upload_process'),
            {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
            follow=True)
        image = Image.objects.all().order_by('-pk')[0]
        # Removing it as the group was autosubmission at this point
        self.group.images.remove(image)

        # Cannot add/remove on autosubmission groups
        response = self.client.post(
            url,
            {
                'images[]': "%d" % image.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 403)

        self.group.autosubmission = False
        self.group.save()

        # Only AJAX allowed
        response = self.client.post(
            url,
            {
                'image': "%d" % image.pk,
            },
            follow=True)
        self.assertEqual(response.status_code, 403)

        # Successfully add
        self.group.members.add(self.user2)
        self.assertEqual(self.group.images.count(), 0)
        updated = self.group.date_updated
        response = self.client.post(
            url,
            {
                'image': "%d" % image.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.group.refresh_from_db()
        self.assertEqual(self.group.images.count(), 1)
        self.assertTrue(self.group.date_updated > updated)
        self.group.members.remove(self.user2)

        response = self.client.get(reverse('image_detail', args=(image.get_id(),)))
        self.assertContains(
            response,
            '<tr><td><a href="%s">%s</a></td></tr>' % (
                reverse('group_detail', args=(self.group.pk, self.group.slug)),
                self.group.name),
            html=True)

    def test_group_remove_member_view(self):
        url = reverse('group_remove_member', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Owner required
        self.client.login(username='user2', password='password')
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.client.login(username='user1', password='password')

        # Group does not exist
        response = self.client.post(reverse('group_remove_member', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Only AJAX allowed
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            follow=True)
        self.assertEqual(response.status_code, 403)

        # User must be member
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user2.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 403)

        # Successfully remove
        self.group.members.add(self.user2)
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user2.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group.members.count(), 1)  # Just user1 left

    def test_group_add_moderator_view(self):
        url = reverse('group_add_moderator', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='user1', password='password')

        # Member required
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)

        self.group.members.add(self.user1)

        # Group does not exist
        response = self.client.post(reverse('group_add_moderator', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Only AJAX allowed
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            follow=True)
        self.assertEqual(response.status_code, 403)

        # Group is not moderated
        self.group.moderated = False
        self.group.save()
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 403)
        self.group.moderated = True
        self.group.save()

        # Successfully add
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user1 in self.group.moderators.all())
        self.assertTrue(self.user1 in self.group.forum.moderators.all())

    def test_group_remove_moderator_view(self):
        url = reverse('group_remove_moderator', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username='user1', password='password')

        # Group does not exist
        response = self.client.post(reverse('group_remove_moderator', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Only AJAX allowed
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            follow=True)
        self.assertEqual(response.status_code, 403)

        # Group is not moderated
        self.group.moderated = False
        self.group.save()
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 403)
        self.group.moderated = True
        self.group.save()

        # User must be moderator
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 403)

        # Successfully remove
        self.group.moderators.add(self.user1)
        response = self.client.post(
            url,
            {
                'user': "%d" % self.user1.pk,
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user1 in self.group.moderators.all())
        self.assertFalse(self.user1 in self.group.forum.moderators.all())

    def test_group_members_list_view(self):
        url = reverse('group_members_list', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Group does not exist
        self.client.login(username='user2', password='password')
        response = self.client.post(reverse('group_remove_moderator', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        # User must be member if the group is private
        self.client.login(username='user2', password='password')
        self.group.public = False
        self.group.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.group.public = True
        self.group.save()
        self.client.logout()

        # Members are rendered in table
        self.client.login(username='user1', password='password')
        self.group.members.add(self.user2)
        response = self.client.get(url)
        self.assertContains(response, self.user2.username)
        self.client.logout()

        # Members list is empty
        self.group.members.clear()
        self.client.login(username='user1', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This group has no members")

    def test_group_moderate_join_requests_view(self):
        url = reverse('group_moderate_join_requests', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Group does not exist
        self.client.login(username='user2', password='password')
        response = self.client.get(reverse('group_moderate_join_requests', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        # Moderator required
        self.client.login(username='user2', password='password')
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        # Group must be moderated
        self.client.login(username='user1', password='password')
        self.group.moderated = False
        self.group.save()
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.group.moderated = True
        self.group.save()
        self.client.logout()

        # Request list is empty
        self.client.login(username='user1', password='password')
        self.group.moderators.add(self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This group has no join requests")
        self.client.logout()

        # Requests are rendered in table
        self.client.login(username='user1', password='password')
        self.group.join_requests.add(self.user2)
        response = self.client.get(url)
        self.assertContains(response, self.user2.username)

    def test_group_approve_join_request_view(self):
        url = reverse('group_approve_join_request', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Group does not exist
        self.client.login(username='user2', password='password')
        response = self.client.get(reverse('group_approve_join_request', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Moderator required
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.group.moderators.add(self.user1)

        # Group must be moderated
        self.client.login(username='user1', password='password')
        self.group.moderated = False
        self.group.save()
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.group.moderated = True
        self.group.save()

        # User must be in the join requests list
        self.client.login(username='user1', password='password')
        response = self.client.post(url, {'user': self.user2.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest', follow=True)
        self.assertEqual(response.status_code, 403)

        self.group.join_requests.add(self.user2)

        # Request must be AJAX
        response = self.client.post(url, {'user': self.user2.pk}, follow=True)
        self.assertEqual(response.status_code, 403)

        # Success
        ToggleProperty.objects.create_toggleproperty("follow", self.user2, self.user1)
        response = self.client.post(url, {'user': self.user2.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user2 in self.group.members.all())
        self.assertFalse(self.user2 in self.group.join_requests.all())

    def test_group_reject_join_request_view(self):
        url = reverse('group_reject_join_request', kwargs={'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Group does not exist
        self.client.login(username='user2', password='password')
        response = self.client.get(reverse('group_reject_join_request', kwargs={'pk': 999}), follow=True)
        self.assertEqual(response.status_code, 404)

        # Moderator required
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        self.group.moderators.add(self.user1)

        # Group must be moderated
        self.client.login(username='user1', password='password')
        self.group.moderated = False
        self.group.save()
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)
        self.group.moderated = True
        self.group.save()

        # User must be in the join requests list
        self.client.login(username='user1', password='password')
        response = self.client.post(url, {'user': self.user2.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest', follow=True)
        self.assertEqual(response.status_code, 403)

        self.group.join_requests.add(self.user2)

        # Request must be AJAX
        response = self.client.post(url, {'user': self.user2.pk}, follow=True)
        self.assertEqual(response.status_code, 403)

        # Success
        response = self.client.post(url, {'user': self.user2.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user2 in self.group.members.all())
        self.assertFalse(self.user2 in self.group.join_requests.all())

    def test_group_autosubmission_sync(self):
        def _upload():
            self.client.login(username='user2', password='password')
            self.client.post(
                reverse('image_upload_process'),
                {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                follow=True)
            self.client.logout()
            return Image.objects_including_wip.all().order_by('-pk')[0]

        group = Group.objects.create(
            name='AS sync test group',
            category=11,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        self.assertEqual(group.members.count(), 1)
        self.assertEqual(group.images.count(), 0)

        # When a member is added to a group, his images are too
        image = _upload()
        group.members.add(self.user2)
        self.assertTrue(image in group.images.all())

        # When an image is deleted, it goes awat from the group
        image.delete()
        self.assertFalse(image in group.images.all())

        # WIP images are NOT added
        image = _upload()
        self.assertTrue(image in group.images.all())
        image.is_wip = True
        image.save(keep_deleted=True)
        self.assertFalse(image in group.images.all())

        # When a member leaves a group, their images are gone
        image.is_wip = False
        image.save(keep_deleted=True)
        self.assertTrue(image in group.images.all())
        group.members.remove(self.user2)
        self.assertFalse(image in group.images.all())

        # When a group changes from autosubmission to non-autosubmission, images are unaffected
        group.members.add(self.user2)
        self.assertTrue(image in group.images.all())
        group.autosubmission = False
        group.save()
        self.assertTrue(image in group.images.all())

        # When a group changes from non-autosubmission to autosubmission, image set is regenerated
        image2 = _upload()
        self.assertTrue(image in group.images.all())
        self.assertFalse(image2 in group.images.all())
        group.autosubmission = True
        group.save()
        self.assertTrue(image in group.images.all())
        self.assertTrue(image2 in group.images.all())
