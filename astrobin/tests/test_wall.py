# Django
from django.core.urlresolvers import reverse
from django.test import TestCase

class WallTest(TestCase):
    def test_page_exists(self):
        response = self.client.get(reverse('wall'))
        self.assertEqual(response.status_code, 200)

        # Check sort menu

        response = self.client.get(reverse('wall') + '?sort=-uploaded')
        self.assertContains(
            response,
            '<a href="?sort=-uploaded"><span class="bg-icon icon-ok"></span>Uploaded</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?sort=-acquired')
        self.assertContains(
            response,
            '<a href="?sort=-acquired"><span class="bg-icon icon-ok"></span>Acquired</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?sort=-views')
        self.assertContains(
            response,
            '<a href="?sort=-views"><span class="bg-icon icon-ok"></span>Views</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?sort=-likes')
        self.assertContains(
            response,
            '<a href="?sort=-likes"><span class="bg-icon icon-ok"></span>Number of likes</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?sort=-bookmarks')
        self.assertContains(
            response,
            '<a href="?sort=-bookmarks"><span class="bg-icon icon-ok"></span>Bookmarks</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?sort=-integration')
        self.assertContains(
            response,
            '<a href="?sort=-integration"><span class="bg-icon icon-ok"></span>Integration</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?sort=-comments')
        self.assertContains(
            response,
            '<a href="?sort=-comments"><span class="bg-icon icon-ok"></span>Comments</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?sort=-uploaded')
        self.assertContains(
            response,
            '<a href="?sort=-uploaded"><span class="bg-icon icon-ok"></span>Uploaded</a>',
            html = True)

        # Check filter menu

        response = self.client.get(reverse('wall') + '?filter=all_ds')
        self.assertContains(
            response,
            '<a href="?filter=all_ds"><span class="bg-icon icon-ok"></span>All deep sky objects</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=all_ss')
        self.assertContains(
            response,
            '<a href="?filter=all_ss"><span class="bg-icon icon-ok"></span>All Solar System objects</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=sun')
        self.assertContains(
            response,
            '<a href="?filter=sun"><span class="bg-icon icon-ok"></span>Sun</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=moon')
        self.assertContains(
            response,
            '<a href="?filter=moon"><span class="bg-icon icon-ok"></span>Moon</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=planets')
        self.assertContains(
            response,
            '<a href="?filter=planets"><span class="bg-icon icon-ok"></span>Planets</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=comets')
        self.assertContains(
            response,
            '<a href="?filter=comets"><span class="bg-icon icon-ok"></span>Comets</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=wide')
        self.assertContains(
            response,
            '<a href="?filter=wide"><span class="bg-icon icon-ok"></span>Extremely wide field</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=trails')
        self.assertContains(
            response,
            '<a href="?filter=trails"><span class="bg-icon icon-ok"></span>Star trails</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=gear')
        self.assertContains(
            response,
            '<a href="?filter=gear"><span class="bg-icon icon-ok"></span>Gear</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=products')
        self.assertContains(
            response,
            '<a href="?filter=products"><span class="bg-icon icon-ok"></span>Commercial products</a>',
            html = True)

        response = self.client.get(reverse('wall') + '?filter=other')
        self.assertContains(
            response,
            '<a href="?filter=other"><span class="bg-icon icon-ok"></span>Other</a>',
            html = True)
