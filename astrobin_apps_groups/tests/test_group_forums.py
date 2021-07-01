# Python

from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase
from pybb.models import Forum, Topic

from astrobin.permissions import CustomForumPermissions
from astrobin.tests.generators import Generators
from astrobin_apps_groups.models import Group


class GroupForumsTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('user1', 'user1@test.com', 'password')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'password')
        self.user3 = User.objects.create_user('user3', 'user3@test.com', 'password')

    def test_public_group_forum_permissions_may_view_forum(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=True,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()

        # Everybody can see the forum.
        self.assertTrue(perms.may_view_forum(AnonymousUser(), group.forum))
        self.assertTrue(perms.may_view_forum(self.user1, group.forum))
        self.assertTrue(perms.may_view_forum(self.user2, group.forum))
        self.assertTrue(perms.may_view_forum(self.user3, group.forum))

    def test_public_group_forum_permissions_filter_forums(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=True,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()

        # Only owner and members can list the forum if paying members.
        self.assertFalse(group.forum in perms.filter_forums(AnonymousUser(), Forum.objects.all()))
        self.assertFalse(group.forum in perms.filter_forums(self.user1, Forum.objects.all()))
        self.assertFalse(group.forum in perms.filter_forums(self.user2, Forum.objects.all()))
        self.assertFalse(group.forum in perms.filter_forums(self.user3, Forum.objects.all()))

        Generators.premium_subscription(self.user1, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user2, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user3, 'AstroBin Ultimate 2020+')

        self.assertFalse(group.forum in perms.filter_forums(AnonymousUser(), Forum.objects.all()))
        self.assertTrue(group.forum in perms.filter_forums(self.user1, Forum.objects.all()))
        self.assertTrue(group.forum in perms.filter_forums(self.user2, Forum.objects.all()))
        self.assertFalse(group.forum in perms.filter_forums(self.user3, Forum.objects.all()))

    def test_public_group_forum_permissions_may_view_topic(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=True,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()
        topic = Topic.objects.create(forum=group.forum, name='Test', user=self.user1)

        # Everybody can see topics.
        self.assertTrue(perms.may_view_topic(AnonymousUser(), topic))
        self.assertTrue(perms.may_view_topic(self.user1, topic))
        self.assertTrue(perms.may_view_topic(self.user2, topic))
        self.assertTrue(perms.may_view_topic(self.user3, topic))

    def test_public_group_forum_permissions_filter_topics(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=True,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()
        topic = Topic.objects.create(forum=group.forum, name='Test', user=self.user1)

        # Everybody can list topics.
        self.assertTrue(topic in perms.filter_topics(AnonymousUser(), Topic.objects.all()))
        self.assertTrue(topic in perms.filter_topics(self.user1, Topic.objects.all()))
        self.assertTrue(topic in perms.filter_topics(self.user2, Topic.objects.all()))
        self.assertTrue(topic in perms.filter_topics(self.user3, Topic.objects.all()))

    def test_public_group_forum_permissions_may_create_topic(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=True,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()

        # Only owner and members can create topics if paying members.
        self.assertFalse(perms.may_create_topic(AnonymousUser(), group.forum))
        self.assertFalse(perms.may_create_topic(self.user1, group.forum))
        self.assertFalse(perms.may_create_topic(self.user2, group.forum))
        self.assertFalse(perms.may_create_topic(self.user3, group.forum))

        Generators.premium_subscription(self.user1, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user2, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user3, 'AstroBin Ultimate 2020+')

        self.assertFalse(perms.may_create_topic(AnonymousUser(), group.forum))
        self.assertTrue(perms.may_create_topic(self.user1, group.forum))
        self.assertTrue(perms.may_create_topic(self.user2, group.forum))
        self.assertFalse(perms.may_create_topic(self.user3, group.forum))

    def test_public_group_forum_permissions_may_create_post(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=True,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()
        topic = Topic.objects.create(forum=group.forum, name='Test', user=self.user1)

        # Only owner and members can create posts if paying members.
        self.assertFalse(perms.may_create_post(AnonymousUser(), topic))
        self.assertFalse(perms.may_create_post(self.user1, topic))
        self.assertFalse(perms.may_create_post(self.user2, topic))
        self.assertFalse(perms.may_create_post(self.user3, topic))

        Generators.premium_subscription(self.user1, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user2, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user3, 'AstroBin Ultimate 2020+')

        self.assertFalse(perms.may_create_post(AnonymousUser(), topic))
        self.assertTrue(perms.may_create_post(self.user1, topic))
        self.assertTrue(perms.may_create_post(self.user2, topic))
        self.assertFalse(perms.may_create_post(self.user3, topic))

    def test_private_group_forum_permissions_may_view_forum(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=False,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()

        # Only owner and members can see the forum.
        self.assertFalse(perms.may_view_forum(AnonymousUser(), group.forum))
        self.assertTrue(perms.may_view_forum(self.user1, group.forum))
        self.assertTrue(perms.may_view_forum(self.user2, group.forum))
        self.assertFalse(perms.may_view_forum(self.user3, group.forum))

    def test_private_group_forum_permissions_filter_forums(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=False,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()

        # Only owner and members can list the forum if paying members.
        self.assertFalse(group.forum in perms.filter_forums(AnonymousUser(), Forum.objects.all()))
        self.assertFalse(group.forum in perms.filter_forums(self.user1, Forum.objects.all()))
        self.assertFalse(group.forum in perms.filter_forums(self.user2, Forum.objects.all()))
        self.assertFalse(group.forum in perms.filter_forums(self.user3, Forum.objects.all()))

        Generators.premium_subscription(self.user1, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user2, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user3, 'AstroBin Ultimate 2020+')

        self.assertFalse(group.forum in perms.filter_forums(AnonymousUser(), Forum.objects.all()))
        self.assertTrue(group.forum in perms.filter_forums(self.user1, Forum.objects.all()))
        self.assertTrue(group.forum in perms.filter_forums(self.user2, Forum.objects.all()))
        self.assertFalse(group.forum in perms.filter_forums(self.user3, Forum.objects.all()))

    def test_private_group_forum_permissions_may_view_topic(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=False,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()
        topic = Topic.objects.create(forum=group.forum, name='Test', user=self.user1)

        # Only owner and members can see topics.
        self.assertFalse(perms.may_view_topic(AnonymousUser(), topic))
        self.assertTrue(perms.may_view_topic(self.user1, topic))
        self.assertTrue(perms.may_view_topic(self.user2, topic))
        self.assertFalse(perms.may_view_topic(self.user3, topic))

    def test_private_group_forum_permissions_filter_topics(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=False,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()
        topic = Topic.objects.create(forum=group.forum, name='Test', user=self.user1)

        # Only owner and members can list topics if paying members.
        self.assertFalse(topic in perms.filter_topics(AnonymousUser(), Topic.objects.all()))
        self.assertFalse(topic in perms.filter_topics(self.user1, Topic.objects.all()))
        self.assertFalse(topic in perms.filter_topics(self.user2, Topic.objects.all()))
        self.assertFalse(topic in perms.filter_topics(self.user3, Topic.objects.all()))

        Generators.premium_subscription(self.user1, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user2, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user3, 'AstroBin Ultimate 2020+')

        self.assertFalse(topic in perms.filter_topics(AnonymousUser(), Topic.objects.all()))
        self.assertTrue(topic in perms.filter_topics(self.user1, Topic.objects.all()))
        self.assertTrue(topic in perms.filter_topics(self.user2, Topic.objects.all()))
        self.assertFalse(topic in perms.filter_topics(self.user3, Topic.objects.all()))

    def test_private_group_forum_permissions_may_create_topic(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=False,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()

        # Only owner and members can create topics if paying members.
        self.assertFalse(perms.may_create_topic(AnonymousUser(), group.forum))
        self.assertFalse(perms.may_create_topic(self.user1, group.forum))
        self.assertFalse(perms.may_create_topic(self.user2, group.forum))
        self.assertFalse(perms.may_create_topic(self.user3, group.forum))

        Generators.premium_subscription(self.user1, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user2, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user3, 'AstroBin Ultimate 2020+')

        self.assertFalse(perms.may_create_topic(AnonymousUser(), group.forum))
        self.assertTrue(perms.may_create_topic(self.user1, group.forum))
        self.assertTrue(perms.may_create_topic(self.user2, group.forum))
        self.assertFalse(perms.may_create_topic(self.user3, group.forum))

    def test_private_group_forum_permissions_may_create_post(self):
        group = Group.objects.create(
            name='Test',
            category=11,
            public=False,
            creator=self.user1,
            owner=self.user1,
            autosubmission=True)
        group.members.add(self.user2)
        perms = CustomForumPermissions()
        topic = Topic.objects.create(forum=group.forum, name='Test', user=self.user1)

        # Only owner and members can create posts if paying members.
        self.assertFalse(perms.may_create_post(AnonymousUser(), topic))
        self.assertFalse(perms.may_create_post(self.user1, topic))
        self.assertFalse(perms.may_create_post(self.user2, topic))
        self.assertFalse(perms.may_create_post(self.user3, topic))

        Generators.premium_subscription(self.user1, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user2, 'AstroBin Ultimate 2020+')
        Generators.premium_subscription(self.user3, 'AstroBin Ultimate 2020+')

        self.assertFalse(perms.may_create_post(AnonymousUser(), topic))
        self.assertTrue(perms.may_create_post(self.user1, topic))
        self.assertTrue(perms.may_create_post(self.user2, topic))
        self.assertFalse(perms.may_create_post(self.user3, topic))
