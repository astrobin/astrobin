# Django
from django.contrib.auth.models import User, Group
from django.test import TestCase

# Third party
from pybb.models import Post, Topic, Forum, Category
from pybb.forms import PostForm
from subscription.models import Subscription, UserSubscription

# AstroBin
from astrobin.templatetags.tags import (
    has_valid_subscription)


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
        g, created = Group.objects.get_or_create(name = "Test group")
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
