# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

# Third party
from beautifulsoupselect import BeautifulSoupSelect as BSS
import simplejson as json

# This app
from astrobin_apps_groups.models import Group

# Other AstroBin apps
from astrobin_apps_notifications.utils import get_unseen_notifications


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
            creator = self.user1,
            owner = self.user1,
            name = 'Test group',
            category = 101,
            public = True,
        )

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()
        self.group.delete()

    def test_misc_ui_elements(self):
        response = self.client.get(reverse('index'))
        bss = BSS(response.content)
        self.assertEqual(len(bss('.explore-menu-groups')), 1)

    def test_public_group_list_view(self):
        response = self.client.get(reverse('public_group_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1>Public groups</h1>', html = True)
        self.assertContains(response, 'Test group')

        self.group.public = False
        self.group.save()

        response = self.client.get(reverse('public_group_list'))
        self.assertNotContains(response, 'Test group')

        self.group.public = True
        self.group.save()

    def test_group_detail_view(self):
        response = self.client.get(reverse('group_detail', kwargs = {'pk': self.group.pk}))
        self.assertEqual(response.status_code, 200)

        self.group.public = False
        self.group.save()
        response = self.client.get(reverse('group_detail', kwargs = {'pk': self.group.pk}))
        self.assertEqual(response.status_code, 403)

        # Restore previous state
        self.group.public = True
        self.group.save()

    def test_group_create_view(self):
        url = reverse('group_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username = 'user1', password = 'password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {
            'name': 'Test create group',
            'description': 'Description',
            'category': 101,
            'public': True,
            'moderated': True,
        }, follow = True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "success unread", "Your new group was created successfully")
        group = Group.objects.all().order_by('-pk')[0]
        self.assertEqual(group.creator, self.user1)
        self.assertEqual(group.owner, self.user1)
        self.assertEqual(group.name, 'Test create group')
        self.assertEqual(group.description, 'Description')
        self.assertEqual(group.category, 101)
        self.assertEqual(group.public, True)
        self.assertEqual(group.moderated, True)
        self.assertTrue(group.owner in group.moderators.all())

        group.delete()
        self.client.logout()

    def test_group_update_view(self):
        url = reverse('group_update', kwargs = {'pk': self.group.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username = 'user2', password = 'password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        self.client.login(username = 'user1', password = 'password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, {
            'name': 'Updated group name',
            'description': 'Updated group description',
            'category': 1,
            'public': False,
            'moderated': True,
        }, follow = True)
        self._assertMessage(response, "success unread", "Form saved")
        self.group = Group.objects.get(pk = self.group.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group.name, 'Updated group name')
        self.assertEqual(self.group.description, 'Updated group description')
        self.assertEqual(self.group.category, 1)
        self.assertEqual(self.group.public, False)
        self.assertEqual(self.group.moderated, True)

        # Restore previous group data
        self.group.name = 'Test group'
        self.group.description = None
        self.group.category = 101
        self.group.public = True
        self.group.moderated = False
        self.group.save()

        self.client.logout()

    def test_group_join_view(self):
        url = reverse('group_join', kwargs = {'pk': self.group.pk})

        # Login required
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.client.login(username = 'user1', password = 'password')

        # GET not allowed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Group does not exist
        response = self.client.post(reverse('group_join', kwargs = {'pk': 999}), follow = True)
        self.assertEqual(response.status_code, 404)

        # Private group, uninvited user
        self.group.public = False; self.group.save()
        response = self.client.post(url, follow = True)
        self.assertEqual(response.status_code, 403)
        self.group.public = True; self.group.save()

        # Public group, but moderated
        self.client.logout()
        self.client.login(username = 'user2', password = 'password')
        self.group.moderated = True; self.group.save()
        self.group.moderators.add(self.group.owner);
        response = self.client.post(url, follow = True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "warning unread", "This is a moderated group, and your join request will be reviewed by a moderator")
        self.assertTrue(len(get_unseen_notifications(self.user1)) > 0)
        self.assertIn("requested to join the group", get_unseen_notifications(self.user1)[0].message)
        self.assertTrue(self.user2 in self.group.join_requests.all())
        self.group.moderated = False; self.group.save()
        self.group.moderators.clear()
        self.client.logout()
        self.client.login(username = 'user1', password = 'password')

        # Join successful
        response = self.client.post(url, follow = True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "success unread", "You have joined the group")
        self.assertTrue(self.user1 in self.group.members.all())

        # Second attempt results in error "already joined"
        response = self.client.post(url, follow = True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "error unread", "You already were a member of this group")
        self.group.members.remove(self.user1)

        # If the group is not public, only invited members can join
        self.group.public = False; self.group.save()

        response = self.client.post(url, follow = True)
        self.assertEqual(response.status_code, 403)

        self.group.invited_users.add(self.user1)

        response = self.client.post(url, follow = True)
        self.assertEqual(response.status_code, 200)
        self._assertMessage(response, "success unread", "You have joined the group")
        self.assertTrue(self.user1 in self.group.members.all())

        # Restore group state
        self.group.invited_users.remove(self.user1)
        self.group.members.remove(self.user1)
        self.group.public = True
        self.group.save()

        self.client.logout()

    def test_group_invite_view(self):
        url = reverse('group_invite', kwargs = {'pk': self.group.pk})
        detail_url = reverse('group_detail', kwargs = {'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Owner required
        self.client.login(username = 'user2', password = 'password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        self.client.login(username = 'user1', password = 'password')

        # GET not allowed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Group does not exist
        response = self.client.post(reverse('group_invite', kwargs = {'pk': 999}), follow = True)
        self.assertEqual(response.status_code, 404)

        # Invited user does not exist
        response = self.client.post(url,
            {
                'users[]': [999],
            },
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertEqual(response.status_code, 200)
        self.group = Group.objects.get(pk = self.group.pk)
        self.assertEqual(self.group.invited_users.count(), 0)

        # Invitation successful
        response = self.client.post(url, {
            'users[]': [self.user2.pk,],
        },)
        self.assertRedirects(response, detail_url, status_code = 302, target_status_code = 200)
        self.group = Group.objects.get(pk = self.group.pk)
        self.assertEqual(self.group.invited_users.count(), 1)
        self.assertEqual(len(get_unseen_notifications(self.user2)), 1)
        self.group.invited_users.clear()

        # AJAX invitation successful
        response = self.client.post(url, {
            'users[]': [self.user2.pk,],
        }, HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.group = Group.objects.get(pk = self.group.pk)
        self.assertEqual(json.loads(response.content)['invited_users'][0]['id'], self.user2.pk)
        self.assertEqual(self.group.invited_users.count(), 1)
        self.assertEqual(len(get_unseen_notifications(self.user2)), 2)

        self.client.logout()

    def test_group_revoke_invitation_view(self):
        url = reverse('group_revoke_invitation', kwargs = {'pk': self.group.pk})

        # Login required
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Owner required
        self.client.login(username = 'user2', password = 'password')
        response = self.client.post(url, follow = True)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

        self.client.login(username = 'user1', password = 'password')

        # GET not allowed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        # Group does not exist
        response = self.client.post(reverse('group_revoke_invitation', kwargs = {'pk': 999}), follow = True)
        self.assertEqual(response.status_code, 404)

        # User does not exist
        response = self.client.post(url,
            {
                'user': "invalid",
            },
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertEqual(response.status_code, 404)

        # Success
        self.group.invited_users.add(self.user2)
        response = self.client.post(url,
            {
                'user': "user2",
            },
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.group.invited_users.count(), 0)

        self.client.logout()
