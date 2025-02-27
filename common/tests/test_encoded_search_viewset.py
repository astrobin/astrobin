import shlex

from django.test import TestCase
from mock import patch

from common.encoded_search_viewset import EncodedSearchViewSet
from common.services.search_service import MatchType


# Dummy query object that supports AND (&) and OR (|) operations.
class DummyQuery:
    def __init__(self, query):
        self.query = query

    def __or__(self, other):
        return DummyQuery(f"({self.query} OR {other.query})")

    def __and__(self, other):
        return DummyQuery(f"({self.query} AND {other.query})")

    def __str__(self):
        return self.query

    def __repr__(self):
        return self.query

# Fake SQS to record filter() and exclude() calls.
class FakeSQS:
    def __init__(self):
        self.filter_calls = []
        self.exclude_calls = []

    def filter(self, query):
        self.filter_calls.append(query)
        return self

    def exclude(self, query):
        self.exclude_calls.append(query)
        return self


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
        original = "M 31"
        expected = '"M 31"'
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, expected)

    def test_prepare_search_value_wrap_inclusions_with_exclusion(self):
        original = "foo M 31 -c"
        expected = 'foo "M 31" -c'
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, expected)

    def test_prepare_search_value_wrap_multiple_groups(self):
        original = "foo M 31 -c d e"
        expected = 'foo "M 31" -c d e'
        result = EncodedSearchViewSet.prepare_search_value(original, MatchType.ALL.value, True)
        self.assertEqual(result, expected)

    def test_prepare_search_value_exclusion_first_then_inclusions(self):
        original = "-c M 31"
        expected = '-c "M 31"'
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

    def test_split_include_terms_inclusion_with_dash_quote(self):
        # Searching for '"a b"' should include "a b"
        terms = ['"a b"']
        include_terms, exclude_terms = EncodedSearchViewSet.split_include_exclude_terms(terms)
        self.assertEqual(include_terms, ['"a b"'])
        self.assertEqual(exclude_terms, [])

    def test_split_exclude_terms_inclusion_with_dash_quote(self):
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

    def test_expand_catalog_term_non_catalog_term(self):
        term = "hello"
        self.assertEqual(EncodedSearchViewSet.expand_catalog_term(term), ["hello"])

    def test_expand_catalog_term_M_catalog_with_space(self):
        term = "M 101"
        expected = ["M101", "M 101"]
        self.assertEqual(set(EncodedSearchViewSet.expand_catalog_term(term)), set(expected))

    def test_expand_catalog_term_M_catalog_without_space(self):
        term = "M101"
        expected = ["M101", "M 101"]
        self.assertEqual(set(EncodedSearchViewSet.expand_catalog_term(term)), set(expected))

    def test_expand_catalog_term_NGC_catalog(self):
        term = "NGC1234"
        expected = ["NGC1234", "NGC 1234"]
        self.assertEqual(set(EncodedSearchViewSet.expand_catalog_term(term)), set(expected))

    def test_expand_catalog_term_Sh2_catalog_with_dash(self):
        term = "Sh2-188"
        expected = ["Sh2-188", "Sh2 188"]
        self.assertEqual(set(EncodedSearchViewSet.expand_catalog_term(term)), set(expected))

    def test_expand_catalog_term_Sh2_catalog_with_space(self):
        term = "Sh2 144"
        expected = ["Sh2-144", "Sh2 144"]
        self.assertEqual(set(EncodedSearchViewSet.expand_catalog_term(term)), set(expected))

    def test_parse_search_query_with_consecutive_single_quotes(self):
        """Test that consecutive single quotes are removed."""
        query = "gso 8''"
        terms = EncodedSearchViewSet.parse_search_query(query)
        # Should parse as two terms: 'gso' and '8'
        self.assertEqual(len(terms), 2)
        self.assertEqual(terms[0], "gso")
        self.assertEqual(terms[1], "8")
        # Most importantly, there should not be any empty terms
        self.assertTrue(all(term.strip() for term in terms))

    def test_parse_search_query_with_consecutive_double_quotes(self):
        """Test that consecutive double quotes are removed."""
        query = 'telescope 10""'
        terms = EncodedSearchViewSet.parse_search_query(query)
        # Should parse as two terms: 'telescope' and '10'
        self.assertEqual(len(terms), 2)
        self.assertEqual(terms[0], "telescope")
        self.assertEqual(terms[1], '10')
        # Most importantly, there should not be any empty terms
        self.assertTrue(all(term.strip() for term in terms))
        
    def test_parse_search_query_with_empty_quotes(self):
        """Test that empty quoted strings are filtered out."""
        query = 'a "" b \'\' c'
        terms = EncodedSearchViewSet.parse_search_query(query)
        # Should only include non-empty terms: 'a', 'b', and 'c'
        self.assertEqual(len(terms), 3)
        self.assertEqual(terms, ["a", "b", "c"])
        
    def test_parse_search_query_with_mixed_quotes(self):
        """Test parsing with mixed single and double quotes."""
        query = 'a "quoted phrase" b \'single quoted\' c'
        terms = EncodedSearchViewSet.parse_search_query(query)
        self.assertEqual(len(terms), 5)
        self.assertEqual(terms, ["a", "\"quoted phrase\"", "b", "'single quoted'", "c"])


class BuildSearchQueryTests(TestCase):
    def setUp(self):
        # Patch SQ and AutoQuery in the module where they are used.
        self.sq_patcher = patch(
            'common.encoded_search_viewset.SQ',
            new=lambda **kwargs: DummyQuery(":".join(f"{k}:{v}" for k, v in kwargs.items()))
        )
        self.autoquery_patcher = patch(
            'common.encoded_search_viewset.AutoQuery',
            new=lambda term: term
        )
        self.sq_patcher.start()
        self.autoquery_patcher.start()
        # Override the static method parse_search_query directly.
        self.orig_parse = EncodedSearchViewSet.parse_search_query
        EncodedSearchViewSet.parse_search_query = staticmethod(lambda value: shlex.split(value))

    def tearDown(self):
        self.sq_patcher.stop()
        self.autoquery_patcher.stop()
        EncodedSearchViewSet.parse_search_query = self.orig_parse

    def test_inclusion_query(self):
        # With matchType ALL and only_search_in_titles_and_descriptions True,
        # prepare_search_value will wrap "M 31" so that parse_search_query returns ['M 31'].
        # Then expand_catalog_term expands "M 31" into ["M31", "M 31"], but when re-prepared,
        # the multi-word variant becomes '"M 31"'.
        query = {'value': 'M 31', 'matchType': MatchType.ALL.value}
        fake = FakeSQS()
        EncodedSearchViewSet.build_search_query(fake, query, only_search_in_titles_and_descriptions=True)
        # Expect one filter() call and no exclude() calls.
        self.assertEqual(len(fake.filter_calls), 1)
        self.assertEqual(len(fake.exclude_calls), 0)
        qstr = str(fake.filter_calls[0])
        # For the single-word variant, we expect no quotes.
        self.assertIn("title:M31", qstr)
        self.assertIn("description:M31", qstr)
        # For the multi-word variant, we now expect the enforced quotes.
        self.assertIn('title:"M 31"', qstr)
        self.assertIn('description:"M 31"', qstr)

    def test_exclusion_query(self):
        # For an exclusion query "-NGC1234", the token becomes "NGC1234" and expands to
        # ["NGC1234", "NGC 1234"] for each field.
        query = {'value': '-NGC1234', 'matchType': MatchType.ANY.value}
        fake = FakeSQS()
        EncodedSearchViewSet.build_search_query(fake, query, only_search_in_titles_and_descriptions=True)
        # No filter() call; expect one exclude() call.
        self.assertEqual(len(fake.filter_calls), 0)
        self.assertEqual(len(fake.exclude_calls), 1)
        qstr = str(fake.exclude_calls[0])
        for expected in ["title:NGC1234", "title:NGC 1234", "description:NGC1234", "description:NGC 1234"]:
            self.assertIn(expected, qstr)

    def test_mixed_query(self):
        # With matchType ALL, "M 31" is wrapped as one token (expanding to both variants)
        # and "-NGC1234" is processed as an exclusion term.
        query = {'value': 'M 31 -NGC1234', 'matchType': MatchType.ALL.value}
        fake = FakeSQS()
        EncodedSearchViewSet.build_search_query(fake, query, only_search_in_titles_and_descriptions=True)
        self.assertEqual(len(fake.filter_calls), 1)
        self.assertEqual(len(fake.exclude_calls), 1)
        inc_str = str(fake.filter_calls[0])
        exc_str = str(fake.exclude_calls[0])
        for expected in ["title:M31", "title:\"M 31\"", "description:M31", "description:\"M 31\""]:
            self.assertIn(expected, inc_str)
        for expected in ["title:NGC1234", "title:\"NGC 1234\"", "description:NGC1234", "description:\"NGC 1234\""]:
            self.assertIn(expected, exc_str)

    def test_multiple_astronomy_catalogs_inclusion(self):
        # Multiple inclusion tokens as quoted phrases.
        query = {'value': '"M 31" "NGC1234" "IC342"', 'matchType': MatchType.ALL.value}
        fake = FakeSQS()
        EncodedSearchViewSet.build_search_query(fake, query, only_search_in_titles_and_descriptions=True)
        self.assertEqual(len(fake.filter_calls), 1)
        self.assertEqual(len(fake.exclude_calls), 0)
        qstr = str(fake.filter_calls[0])
        for expected in ["title:M31", "title:\"M 31\"", "description:M31", "description:\"M 31\""]:
            self.assertIn(expected, qstr)
        for expected in ["title:NGC1234", "title:\"NGC 1234\"", "description:NGC1234", "description:\"NGC 1234\""]:
            self.assertIn(expected, qstr)
        for expected in ["title:IC342", "title:\"IC 342\"", "description:IC342", "description:\"IC 342\""]:
            self.assertIn(expected, qstr)

    def test_multiple_astronomy_catalogs_exclusion(self):
        # Multiple exclusion tokens. The current implementation calls exclude() per token.
        query = {'value': '-NGC1234 -IC342', 'matchType': MatchType.ANY.value}
        fake = FakeSQS()
        EncodedSearchViewSet.build_search_query(fake, query, only_search_in_titles_and_descriptions=True)
        # Expect two separate exclude() calls.
        self.assertEqual(len(fake.exclude_calls), 2)
        # Verify each call contains the expected variants.
        for call in fake.exclude_calls:
            call_str = str(call)
            if "NGC" in call_str:
                for expected in ["title:NGC1234", "title:NGC 1234", "description:NGC1234", "description:NGC 1234"]:
                    self.assertIn(expected, call_str)
            elif "IC" in call_str:
                for expected in ["title:IC342", "title:IC 342", "description:IC342", "description:IC 342"]:
                    self.assertIn(expected, call_str)
    
    def test_consecutive_single_quotes_in_search_value(self):
        """Test the specific bug fix for 'gso 8'' issue."""
        query = {'value': "gso 8''", 'matchType': MatchType.ALL.value}
        fake = FakeSQS()
        
        # Let the actual implementation parse the query
        EncodedSearchViewSet.build_search_query(fake, query)
        
        # Verify that there's exactly one filter call and no exclude calls
        self.assertEqual(len(fake.filter_calls), 1)
        self.assertEqual(len(fake.exclude_calls), 0)
        
        # Get the query string
        qstr = str(fake.filter_calls[0])
        
        # Verify the query contains text:gso and text:8 (no quotes)
        self.assertIn("text:gso", qstr)
        self.assertIn("text:8", qstr)
        
        # Make sure we don't have empty text: terms
        parts = qstr.replace("(", "").split(")")
        for part in parts:
            if "text:" in part:
                # Ensure no empty query terms (this was the bug - empty text:)
                self.assertNotEqual(part.strip(), "text:")

    def test_quotes_wrapping_everything(self):
        """Test that the entire query is wrapped in quotes."""
        query = {'value': '"a b c"', 'matchType': MatchType.ALL.value}
        fake = FakeSQS()
        EncodedSearchViewSet.build_search_query(fake, query)
        self.assertEqual(len(fake.filter_calls), 1)
        self.assertEqual(len(fake.exclude_calls), 0)
        qstr = str(fake.filter_calls[0])
        self.assertEqual(qstr, 'text:"a b c"')
