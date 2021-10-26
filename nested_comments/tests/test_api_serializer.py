from django.test import TestCase

from nested_comments.serializers import NestedCommentSerializer
from nested_comments.tests.nested_comments_generators import NestedCommentsGenerators


class NestedCommentApiSerializerTest(TestCase):
    def test_html(self):
        comment = NestedCommentsGenerators.comment(text='[b]Test comment[/b]')
        serializer = NestedCommentSerializer(instance=comment)
        representation = serializer.to_representation(comment)
        self.assertEqual(comment.text, representation.get('text'))
        self.assertEqual('<strong>Test comment</strong>', representation.get('html'))
