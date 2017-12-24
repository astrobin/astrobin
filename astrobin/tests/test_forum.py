# Django
from django.contrib.auth.models import User, Group
from django.test import TestCase

# Third party
from pybb.models import Post, Topic, Forum, Category
from pybb.forms import PostForm
from subscription.models import Subscription, UserSubscription

# AstroBin
from astrobin_apps_groups.models import Group as AstroBinGroup
from astrobin.templatetags.tags import (
    has_valid_subscription)
from astrobin.permissions import CustomForumPermissions


class ForumTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username = "user", email = "user@example.com",
            password = "password")

        self.category = Category.objects.create(name = "Test category")
        self.forum = Forum.objects.create(name = "Test forum", category = self.category)

        self.client.login(username = "user", password = "password")


    def tearDown(self):
        self.forum.delete()
        self.category.delete()
        self.user.delete()


    def _get_post_form(self):
        topic = Topic(
            forum = self.forum, name = "Test topic", user = self.user)
        post = Post(topic = topic, user = self.user)
        form = PostForm(instance = post, user = self.user, topic = topic)
        form.cleaned_data = {
            'name': "Test topic",
            'body': "Test",
            'poll_type': 0,
            'poll_question': None,
        }
        return form


    def test_create_post_requires_moderation(self):
        form = self._get_post_form()
        post, topic = form.save(commit = False)

        self.assertEqual(post.on_moderation, True)


    def test_create_post_premium(self):
        # Premium members have a free pass
        g, created = Group.objects.get_or_create(name = "astrobin_premium")
        s, created = Subscription.objects.get_or_create(
            name = "AstroBin Premium",
            price = 1,
            group = g,
            category = "premium")
        us, created = UserSubscription.objects.get_or_create(
            user = self.user,
            subscription = s)

        us.subscribe()
        self.assertEqual(has_valid_subscription(self.user, s.pk), True)

        form = self._get_post_form()
        post, topic = form.save(commit = False)

        self.assertEqual(post.on_moderation, False)

        us.delete()
        s.delete()
        g.delete()


    def test_create_post_high_index(self):
        with self.settings(MIN_INDEX_TO_LIKE = 0):
            form = self._get_post_form()
            post, topic = form.save(commit = False)

            self.assertEqual(post.on_moderation, False)


    def test_create_post_multiple_approved(self):
        for i in range(0,5):
            form = self._get_post_form()
            post, topic = form.save(commit = True)
            post.on_moderation = False
            post.save()

        form = self._get_post_form()
        post, topic = form.save(commit = False)

        self.assertEqual(post.on_moderation, False)


    def test_may_view_topic(self):
        topic = Topic.objects.create(
            forum = self.forum, name = "Test topic", user = self.user)

        post = Post.objects.create(
            topic = topic, user = self.user, body = "Test post")

        user2 = User.objects.create_user(
            username = "user2", email = "user2@example.com",
            password = "password")

        perms = CustomForumPermissions()

        # Unauthenticated
        self.assertTrue(perms.may_view_topic(user2, topic))

        # Authenticated
        self.client.login(username = "user2", password = "password")
        self.assertTrue(perms.may_view_topic(user2, topic))

        # Topic in forum that belongs to public group and user2 is not a member
        group = AstroBinGroup.objects.create(
            creator = self.user,
            owner = self.user,
            name = "Test group",
            category = 101,
            public = True,
            forum = self.forum)
        self.assertFalse(perms.may_view_topic(user2, topic))

        # user2 becomes a subscriber
        topic.subscribers.add(user2)
        self.assertTrue(perms.may_view_topic(user2, topic))

        # user2 not a subscriber, but a member of the group
        topic.subscribers.remove(user2)
        group.members.add(user2)
        self.assertTrue(perms.may_view_topic(user2, topic))

        # group owner
        group.members.remove(user2)
        group.owner = user2
        group.save()
        self.assertTrue(perms.may_view_topic(user2, topic))

        # Restore status
        self.client.logout()
        self.client.login(username = "user", password = "password")

        user2.delete()
        post.delete()
        group.delete()
