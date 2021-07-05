from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase
from pybb.models import Topic, Forum, Category

from astrobin.permissions import CustomForumPermissions


class ForumPermissionsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@test.com', 'password')
        self.forum = Forum.objects.create(name='test', category=Category.objects.create(name='test'))
        self.topic = Topic.objects.create(forum=self.forum, name='test', user=self.user)
        self.perms = CustomForumPermissions()

    def test_forum_permissions_may_view_forum(self):
        # Everybody can see the forum.
        self.assertTrue(self.perms.may_view_forum(AnonymousUser(), self.forum))
        self.assertTrue(self.perms.may_view_forum(self.user, self.forum))

    def test_forum_permissions_filter_forums(self):
        # Everybody list the forum.
        self.assertTrue(self.forum in self.perms.filter_forums(AnonymousUser(), Forum.objects.all()))
        self.assertTrue(self.forum in self.perms.filter_forums(self.user, Forum.objects.all()))

    def test_forum_permissions_may_view_topic(self):
        # Everybody can see topics.
        self.assertTrue(self.perms.may_view_topic(AnonymousUser(), self.topic))
        self.assertTrue(self.perms.may_view_topic(self.user, self.topic))

    def test_forum_permissions_filter_topics(self):
        # Everybody can list topics.
        self.assertTrue(self.topic in self.perms.filter_topics(AnonymousUser(), Topic.objects.all()))
        self.assertTrue(self.topic in self.perms.filter_topics(self.user, Topic.objects.all()))

    def test_forum_permissions_may_create_topic(self):
        # Everybody can create topics.
        self.assertFalse(self.perms.may_create_topic(AnonymousUser(), self.forum))
        self.assertTrue(self.perms.may_create_topic(self.user, self.forum))

    def test_forum_permissions_may_create_post(self):
        # Everybody may create posts.
        self.assertFalse(self.perms.may_create_post(AnonymousUser(), self.topic))
        self.assertTrue(self.perms.may_create_post(self.user, self.topic))
