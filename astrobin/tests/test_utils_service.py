from django.test import TestCase

from astrobin.services.utils_service import UtilsService


class UtilsServiceTest(TestCase):
    def test_unique(self):
        self.assertEqual([], UtilsService.unique([]))
        self.assertEqual([1], UtilsService.unique([1]))
        self.assertEqual([1], UtilsService.unique([1, 1]))
        self.assertEqual([1, 2], UtilsService.unique([1, 2]))
        self.assertEqual([1, 2], UtilsService.unique([1, 2, 1]))
        self.assertEqual([2, 1], UtilsService.unique([2, 1, 2]))

    def test_split_text_alphanumerically(self):
        self.assertEqual([], UtilsService.split_text_alphanumerically(''))
        self.assertEqual(['a'], UtilsService.split_text_alphanumerically('a'))
        self.assertEqual(['a', '1'], UtilsService.split_text_alphanumerically('a1'))
        self.assertEqual(['a', '1', 'b'], UtilsService.split_text_alphanumerically('a1b'))
        self.assertEqual(['a', '1', 'b'], UtilsService.split_text_alphanumerically('a 1 b'))

    def test_get_search_synonyms_text_match(self):
        self.assertEqual(
            UtilsService.get_search_synonyms_text('A beautiful view of the Crab Nebula'),
            'messier 1,sharpless 244,taurus a,crab nebula,crab neb,crab,sh 2 244,ngc 1952,m 1'
        )

        self.assertEqual(
            UtilsService.get_search_synonyms_text('This image shows the famous Andromeda Galaxy'),
            'andromeda galaxy,messier 31,andromeda,m 31,andromeda nebula,and nebula,ngc 224,ugc 454'
        )

    def test_get_search_synonyms_text_no_match(self):
        self.assertIsNone(UtilsService.get_search_synonyms_text('Galactic Core'))

    def test_get_search_synonyms_text_partial_match_not_valid(self):
        self.assertIsNone(UtilsService.get_search_synonyms_text('Galaxy NGC'))
