from unittest import mock

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

    # Real implementation tests for detect_language
    def test_detect_language_empty_text(self):
        self.assertIsNone(UtilsService.detect_language(''))
        self.assertIsNone(UtilsService.detect_language('   '))
        self.assertIsNone(UtilsService.detect_language(None))

    def test_detect_language_short_text(self):
        self.assertIsNone(UtilsService.detect_language('hi'))
        self.assertIsNone(UtilsService.detect_language('hi there'))

    def test_detect_language_english(self):
        result = UtilsService.detect_language('This is a sample text in English with enough characters to detect.')
        self.assertEqual(result, 'en')

    def test_detect_language_spanish(self):
        result = UtilsService.detect_language(
            'Este es un texto de ejemplo en español con suficientes caracteres para detectar.'
        )
        self.assertEqual(result, 'es')

    def test_detect_language_italian(self):
        result = UtilsService.detect_language(
            'Questo è un testo di esempio in italiano con caratteri sufficienti per rilevare.'
        )
        self.assertEqual(result, 'it')

    def test_detect_language_french(self):
        result = UtilsService.detect_language(
            'Ceci est un exemple de texte en français avec suffisamment de caractères pour détecter.'
        )
        self.assertEqual(result, 'fr')

    def test_detect_language_with_bbcode(self):
        result = UtilsService.detect_language(
            '[b]This is a sample text[/b] in [i]English[/i] with enough characters to detect.'
        )
        self.assertEqual(result, 'en')

    def test_detect_language_with_html(self):
        result = UtilsService.detect_language(
            '<strong>This is a sample text</strong> in <em>English</em> with enough characters to detect.'
        )
        self.assertEqual(result, 'en')
        
    # Mock tests for detect_language to isolate behavior
    @mock.patch('astrobin.services.utils_service._LANGUAGE_DETECTOR')
    def test_detect_language_with_lingua_mock(self, mock_detector):
        # Setup a mock language result
        mock_language = mock.MagicMock()
        mock_language.iso_code_639_1.name.lower.return_value = 'de'
        mock_detector.detect_language_of.return_value = mock_language

        result = UtilsService.detect_language('Some text to test')
        self.assertEqual(result, 'de')
        mock_detector.detect_language_of.assert_called_once()

    @mock.patch('astrobin.services.utils_service._LANGUAGE_DETECTOR')
    def test_detect_language_lingua_returns_none(self, mock_detector):
        # Setup lingua to return None (detection failed)
        mock_detector.detect_language_of.return_value = None

        # Setup langdetect to succeed as fallback
        with mock.patch('astrobin.services.utils_service.langdetect_detect', return_value='ja'):
            result = UtilsService.detect_language('Some text to test')
            self.assertEqual(result, 'ja')
            mock_detector.detect_language_of.assert_called_once()

    @mock.patch('astrobin.services.utils_service._LANGUAGE_DETECTOR')
    def test_detect_language_lingua_throws_exception(self, mock_detector):
        # Setup lingua to throw an exception
        mock_detector.detect_language_of.side_effect = Exception('Lingua error')

        # Setup langdetect to succeed as fallback
        with mock.patch('astrobin.services.utils_service.langdetect_detect', return_value='ru'):
            result = UtilsService.detect_language('Some text to test')
            self.assertEqual(result, 'ru')
            mock_detector.detect_language_of.assert_called_once()

    @mock.patch('astrobin.services.utils_service._LANGUAGE_DETECTOR')
    @mock.patch('astrobin.services.utils_service.langdetect_detect')
    def test_detect_language_both_fail(self, mock_langdetect, mock_detector):
        # Setup lingua to throw an exception
        mock_detector.detect_language_of.side_effect = Exception('Lingua error')

        # Setup langdetect to also fail
        mock_langdetect.side_effect = Exception('Langdetect error')

        result = UtilsService.detect_language('Some text to test')
        self.assertEqual('en', result)
        mock_detector.detect_language_of.assert_called_once()
        mock_langdetect.assert_called_once()
