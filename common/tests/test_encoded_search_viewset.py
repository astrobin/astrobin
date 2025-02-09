from django.test import TestCase

from common.encoded_search_viewset import EncodedSearchViewSet
from common.services.search_service import MatchType


class EncodedSearchViewSetTests(TestCase):
    def test_prepare_search_value_only_search_false_returns_original(self):
        original = "a b -c d e"
        # When only_search_in_titles_and_descriptions is False, value should be unchanged.
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, False)
        self.assertEqual(result, original)

    def test_prepare_search_value_match_type_not_all_returns_original(self):
        original = "a b -c d e"
        # When match_type is not ALL, value should be unchanged.
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ANY.value, True)
        self.assertEqual(result, original)

    def test_prepare_search_value_query_already_contains_quotes_returns_original(self):
        original = '"a b" c'
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, original)

    def test_prepare_search_value_wrap_contiguous_inclusions_two_words(self):
        original = "a b"
        expected = '"a b"'
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, expected)

    def test_prepare_search_value_wrap_inclusions_with_exclusion(self):
        original = "a b -c"
        expected = '"a b" -c'
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, expected)

    def test_prepare_search_value_wrap_multiple_groups(self):
        original = "a b -c d e"
        expected = '"a b" -c "d e"'
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, expected)

    def test_prepare_search_value_exclusion_first_then_inclusions(self):
        original = "-c a b"
        expected = '-c "a b"'
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, expected)

    def test_prepare_search_value_single_token_unchanged(self):
        original = "a"
        expected = "a"
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, expected)

    def test_split_include_exclude_terms_simple(self):
        terms = ["a", "b"]
        include_terms, exclude_terms = EncodedSearchViewSet.split_include_exclude_terms(terms)
        self.assertEqual(include_terms, ["a", "b"])
        self.assertEqual(exclude_terms, [])

    def test_split_include_exclude_terms_all_exclusion(self):
        terms = ["-c", "-d"]
        include_terms, exclude_terms = EncodedSearchViewSet.split_include_exclude_terms(terms)
        self.assertEqual(include_terms, [])
        self.assertEqual(exclude_terms, ["c", "d"])

    def test_split_include_exclude_terms_inclusion_with_dash_quote(self):
        # Searching for '-"a b"' should exclude "a b"
        terms = ['-"a b"']
        include_terms, exclude_terms = EncodedSearchViewSet.split_include_exclude_terms(terms)
        self.assertEqual(include_terms, [])
        self.assertEqual(exclude_terms, ['"a b"'])

    def test_split_include_exclude_terms_mixed(self):
        terms = ["a", '-"b c"', "-d", "e", '-"f g h"', "-i"]
        include_terms, exclude_terms = EncodedSearchViewSet.split_include_exclude_terms(terms)
        self.assertEqual(include_terms, ["a", "e"])
        self.assertEqual(exclude_terms, ['"b c"', "d", '"f g h"', "i"])
