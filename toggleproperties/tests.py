from django.contrib.auth.models import User
from django.test import TestCase

from models import ToggleProperty


class TogglePropertyTest(TestCase):
    def setUp(self):
        self.alice = User.objects.create(username="alice")
        self.bob = User.objects.create(username="bob")

    def testAddToggleProperty(self):
        # alice likes bob
        like = ToggleProperty.objects.create_toggleproperty("like", self.bob, self.alice)

        self.assertEquals(like.user, self.alice)
        self.assertEquals(like.content_object, self.bob)

        # alice likes the like
        meta_like = ToggleProperty.objects.create_toggleproperty("like", like, self.alice)

        self.assertEquals(meta_like.user, self.alice)
        self.assertEquals(meta_like.content_object, like)

    def testGetTogglePropertiesForUser(self):
        # alice likes bob
        ToggleProperty.objects.create_toggleproperty("like", self.bob, self.alice)
        likes = ToggleProperty.objects.toggleproperties_for_user("like", self.alice)

        self.assertEquals(len(likes), 1)
        self.assertEquals(likes[0].content_object, self.bob)

    def testGetTogglePropertiesForModel(self):
        # alice likes bob
        ToggleProperty.objects.create_toggleproperty("like", self.bob, self.alice)

        likes = ToggleProperty.objects.toggleproperties_for_model("like", User)

        self.assertEquals(len(likes), 1)
        self.assertEquals(likes[0].user, self.alice)

    def testGetTogglePropertiesForObject(self):
        # alice likes bob
        ToggleProperty.objects.create_toggleproperty("like", self.bob, self.alice)

        likes = ToggleProperty.objects.toggleproperties_for_object("like", self.bob)
        self.assertEquals(len(likes), 1)
        self.assertEquals(likes[0].user, self.alice)

    def testCreatingMultiple(self):
        # alice likes bob, twice
        ToggleProperty.objects.create_toggleproperty("like", self.bob, self.alice)
        ToggleProperty.objects.create_toggleproperty("like", self.bob, self.alice)

        likes = ToggleProperty.objects.toggleproperties_for_object("like", self.bob)
        self.assertEquals(len(likes), 1)
        self.assertEquals(likes[0].user, self.alice)
