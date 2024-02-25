import mock
from django.contrib.auth.models import AnonymousUser, User, Group
from django.urls import reverse
from django.test import TestCase, override_settings
from mock import patch
from pybb.forms import PostForm
from pybb.models import Post, Topic, Forum, Category
from subscription.models import Subscription, UserSubscription

from astrobin.models import UserProfile
from astrobin.permissions import CustomForumPermissions
from astrobin.templatetags.tags import (
    forum_latest_topics, has_valid_subscription,
)
from astrobin.tests.generators import Generators
from astrobin_apps_groups.models import Group as AstroBinGroup
from astrobin_apps_premium.services.premium_service import SubscriptionName


class ForumTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user", email="user@example.com",
            password="password")

        self.moderator = User.objects.create_user(
            username="moderator", email="moderator@example.com",
            password="password")

        self.content_moderators = Group.objects.create(name='content_moderators')
        self.moderator.groups.add(self.content_moderators)

        self.category = Category.objects.create(name="Test category")
        self.forum = Forum.objects.create(name="Test forum", category=self.category)

        self.client.login(username="user", password="password")


    def _get_post_form(self, user=None, topic=None):
        if topic is None:
            topic = Topic(forum=self.forum, name="Test topic", user=self.user if not user else user)
        post = Post(topic=topic, user=self.user if not user else user)
        form = PostForm(instance=post, user=self.user if not user else user, topic=topic)
        form.cleaned_data = {
            'name': "Test topic",
            'body': "Test",
            'poll_type': 0,
            'poll_question': None,
        }
        return form

    def test_create_post_requires_moderation(self):
        form = self._get_post_form()
        post, topic = form.save(commit=False)

        self.assertEqual(post.on_moderation, True)

    def test_create_post_auto_approve_domain(self):
        old_email = self.user.email
        self.user.email = 'test@highpointscientific.com'
        self.user.save()

        form = self._get_post_form()
        post, topic = form.save(commit=False)

        self.assertEqual(post.on_moderation, False)

        self.user.email = old_email
        self.user.save()

    def test_create_post_premium(self):
        # Premium members have a free pass
        g, created = Group.objects.get_or_create(name="astrobin_premium")
        s, created = Subscription.objects.get_or_create(
            name=SubscriptionName.PREMIUM_CLASSIC.value,
            price=1,
            group=g,
            category="premium")
        us, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=s)

        us.subscribe()
        self.assertEqual(has_valid_subscription(self.user, s.pk), True)

        form = self._get_post_form()
        post, topic = form.save(commit=False)

        self.assertEqual(post.on_moderation, False)

    def test_create_post_premium_from_russia(self):
        user = Generators.user()
        user.userprofile.last_seen_in_country = 'ru'
        user.userprofile.save()

        Generators.premium_subscription(user, SubscriptionName.PREMIUM_2020)

        form = self._get_post_form()
        post, topic = form.save(commit=False)

        self.assertEqual(post.on_moderation, True)

    @patch('astrobin.models.UserProfile.get_scores')
    def test_create_post_high_index(self, get_scores):
        get_scores.return_value = {
            'user_scores_index': 1000
        }

        form = self._get_post_form()
        post, topic = form.save(commit=False)

        # Index doesn't matter, you still get moderated.
        self.assertEqual(post.on_moderation, True)

    @patch('astrobin.models.UserProfile.get_scores')
    def test_create_post_multiple_approved_but_not_enough(self, get_scores):
        get_scores.return_value = {
            'user_scores_index': 0
        }

        form = self._get_post_form(Generators.user())
        post, topic = form.save(commit=True)
        topic.on_moderation = False
        topic.save()
        post.on_moderation = False
        post.save()

        for i in range(0, 2):
            form = self._get_post_form(self.user, topic)
            post, topic = form.save(commit=True)
            post.on_moderation = False
            post.save()

        form = self._get_post_form()
        post, topic = form.save(commit=False)

        self.assertEqual(post.on_moderation, True)

    @patch('astrobin.models.UserProfile.get_scores')
    def test_create_post_multiple_approved(self, get_scores):
        get_scores.return_value = {
            'user_scores_index': 0
        }

        form = self._get_post_form(Generators.user())
        post, topic = form.save(commit=True)
        topic.on_moderation = False
        topic.save()
        post.on_moderation = False
        post.save()

        for i in range(0, 5):
            form = self._get_post_form(self.user, topic)
            post, topic = form.save(commit=True)
            post.on_moderation = False
            post.save()

        form = self._get_post_form()
        post, topic = form.save(commit=False)

        self.assertEqual(post.on_moderation, False)

    def test_may_view_topic(self):
        topic = Topic.objects.create(
            forum=self.forum, name="Test topic", user=self.user)

        post = Post.objects.create(
            topic=topic, user=self.user, body="Test post")

        user2 = User.objects.create_user(
            username="user2", email="user2@example.com",
            password="password")

        perms = CustomForumPermissions()

        # Unauthenticated
        self.assertTrue(perms.may_view_topic(user2, topic))

        # Authenticated
        self.client.login(username="user2", password="password")
        self.assertTrue(perms.may_view_topic(user2, topic))

        # Topic in forum that belongs to public group and user2 is not a member
        group = AstroBinGroup.objects.create(
            creator=self.user,
            owner=self.user,
            name="Test group",
            category=101,
            public=True,
            forum=self.forum)
        self.assertTrue(perms.may_view_topic(user2, topic))

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
        self.client.login(username="user", password="password")

    def test_mark_as_spam(self):
        topic1 = Topic.objects.create(forum=self.forum, name="Test topic 1", user=self.user)
        topic2 = Topic.objects.create(forum=self.forum, name="Test topic 2", user=self.user)

        self.client.login(username="moderator", password="password")

        response = self.client.post(
            reverse('forum_moderation_mark_as_spam'),
            {
                "topic-ids[]": [topic1.id, topic2.id]
            },
            follow=True)

        self.assertContains(response, "2 topics deleted")
        self.assertEqual(1, Topic.objects.filter(id=topic1.id).count())
        self.assertEqual(1, Topic.objects.filter(id=topic2.id).count())
        self.assertEqual(0, UserProfile.objects.filter(user=self.user).count())

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.push_notification")
    def test_save_new_notifications(self, push_notification, get_mentions):
        mentioned = Generators.user()

        get_mentions.return_value = [mentioned]

        post = Generators.forum_post()

        push_notification.assert_has_calls([
            mock.call([mentioned], post.user, 'new_forum_post_mention', mock.ANY),
        ], any_order=True)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, post.user, 'new_forum_reply', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([post.user], None, 'forum_post_approved', mock.ANY)

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.push_notification")
    def test_save_existing_notifications(self, push_notification, get_mentions):
        mentioned = Generators.user()

        get_mentions.return_value = [mentioned]

        post = Generators.forum_post()

        push_notification.reset_mock()
        get_mentions.reset_mock()

        post.body = "foo"
        post.save()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([mentioned], post.user, 'new_forum_post_mention', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, post.user, 'new_forum_reply', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([post.user], None, 'forum_post_approved', mock.ANY)

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.push_notification")
    def test_save_new_on_moderation_notifications(self, push_notification, get_mentions):
        mentioned = Generators.user()

        get_mentions.return_value = [mentioned]

        post = Generators.forum_post(on_moderation=True)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([mentioned], post.user, 'new_forum_post_mention', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, post.user, 'new_forum_reply', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([post.user], None, 'forum_post_approved', mock.ANY)

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.push_notification")
    def test_save_existing_on_moderation_notifications(self, push_notification, get_mentions):
        mentioned = Generators.user()

        get_mentions.return_value = [mentioned]

        post = Generators.forum_post(on_moderation=True)

        push_notification.reset_mock()
        get_mentions.reset_mock()

        post.body = "foo"
        post.save()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([mentioned], post.user, 'new_forum_post_mention', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, post.user, 'new_forum_reply', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([post.user], None, 'forum_post_approved', mock.ANY)

    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    })
    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.push_notification")
    def test_save_existing_and_approve_notifications(self, push_notification, get_mentions):
        mentioned = Generators.user()

        get_mentions.return_value = [mentioned]

        post = Generators.forum_post(on_moderation=True)

        push_notification.reset_mock()
        get_mentions.reset_mock()

        post.on_moderation = False
        post.save()

        push_notification.assert_has_calls([
            mock.call([mentioned], post.user, 'new_forum_post_mention', mock.ANY),
            mock.call([post.user], None, 'forum_post_approved', mock.ANY),
        ], any_order=True)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, post.user, 'new_forum_reply', mock.ANY)

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }
    )
    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.push_notification")
    def test_does_not_send_self_mention_notification(self, push_notification, get_mentions):
        mentioned: User = Generators.user()

        get_mentions.return_value = [mentioned.username]

        post = Generators.forum_post(user=mentioned)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([mentioned], post.user, 'new_forum_post_mention', mock.ANY)

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }
    )
    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.push_notification")
    def test_does_not_send_self_mention_notification_on_edit(self, push_notification, get_mentions):
        mentioned: User = Generators.user()
        post = Generators.forum_post(user=mentioned)

        get_mentions.return_value = [mentioned.username]
        post.save()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([mentioned], post.user, 'new_forum_post_mention', mock.ANY)

    @patch("astrobin.signals.push_notification")
    def test_send_reply_notifications(self, push_notification):
        post = Generators.forum_post()

        reply1 = Generators.forum_post(topic=post.topic)

        push_notification.assert_called_with([post.user], reply1.user, 'new_forum_reply_started_topic', mock.ANY)

        reply2 = Generators.forum_post(topic=post.topic)

        push_notification.assert_has_calls([
            mock.call([post.user], reply2.user, 'new_forum_reply_started_topic', mock.ANY),
            mock.call([reply1.user], reply2.user, 'new_forum_reply', mock.ANY),
        ], any_order=True)

    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.push_notification")
    def test_does_not_send_new_forum_reply_started_topic_if_starter_is_mentioned(self, push_notification, get_mentions):
        post = Generators.forum_post()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([post.user], post.user, 'new_forum_reply_started_topic', mock.ANY)

        get_mentions.reset_mock()
        push_notification.reset_mock()
        get_mentions.return_value = [post.user.username]

        reply = Generators.forum_post(topic=post.topic)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([post.user], reply.user, 'new_forum_reply_started_topic', mock.ANY)

        push_notification.assert_called_with([post.user], reply.user, 'new_forum_post_mention', mock.ANY)

    def test_forum_latest_topics(self):
        Generators.forum_topic(on_moderation=True)
        user = Generators.user()

        self.assertEqual(0, forum_latest_topics({}, user).count())

        g, _ = Group.objects.get_or_create(name="forum_moderators")
        g.user_set.add(user)

        self.assertEqual(1, forum_latest_topics({}, user).count())

    def test_forum_latest_topics_anon(self):
        Generators.forum_topic(on_moderation=True)
        user = AnonymousUser()

        self.assertEqual(0, forum_latest_topics({}, user).count())
