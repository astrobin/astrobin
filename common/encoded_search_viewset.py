import base64
import json
import re
import zlib
from urllib.parse import parse_qs, unquote

import msgpack
from drf_haystack.viewsets import HaystackViewSet
from haystack.backends import SQ
from haystack.inputs import AutoQuery
from rest_framework.exceptions import ParseError

from common.services.search_service import MatchType


class EncodedSearchViewSet(HaystackViewSet):
    decoded_query_params = {}

    @staticmethod
    def decode_base64_padding(base64_string: str) -> str:
        # Add padding if necessary
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += '=' * (4 - missing_padding)
        return base64_string

    @staticmethod
    def simplify_one_item_lists(params):
        return {
            key: value[0]
            if isinstance(value, list) and len(value) == 1
            else value
            for key, value in params.items()
        }

    @staticmethod
    def preprocess_query_params(params):
        for key in params.keys():
            value = params[key]
            if isinstance(value, bool):
                value = 'true' if value else 'false'
            elif isinstance(value, str) and value.lower() in ('true', 'false'):
                value = value.lower()
            params[key] = value

        return params

    @staticmethod
    def update_request_params(request, params):
        request._request.GET = request._request.GET.copy()
        for key, value in params.items():
            request._request.GET[key] = value
        return request

    @staticmethod
    def parse_search_query(query):
        # First, strip out consecutive empty quotes ('' or "")
        query = query.replace("''", "").replace('""', "")
        
        terms = []
        current_term = []
        in_quotes = None  # None, '"' or "'"
        i = 0

        while i < len(query):
            char = query[i]

            # Handle quotes
            if char in '"\'':
                if in_quotes == char:  # Closing quote
                    current_term.append(char)
                    if current_term:
                        terms.append(''.join(current_term))
                    current_term = []
                    in_quotes = None
                elif in_quotes is None:  # Opening quote
                    if current_term:  # Save any accumulated non-quoted term
                        terms.append(''.join(current_term))
                    current_term = [char]
                    in_quotes = char
                else:  # Quote within another type of quote
                    current_term.append(char)

            # Handle spaces
            elif char.isspace():
                if in_quotes:  # Space within quotes
                    current_term.append(char)
                elif current_term:  # Space outside quotes - terminate current term
                    terms.append(''.join(current_term))
                    current_term = []

            # Handle all other characters
            else:
                current_term.append(char)

            i += 1

        # Handle any remaining term and unclosed quotes
        if current_term:
            terms.append(''.join(current_term))

        return [term for term in terms if term.strip()]

    @staticmethod
    def is_astronomy_catalog(term):
        # Return True if term exactly matches one of the known catalog patterns.
        if re.match(r'^(Sh2)[-\s]?(\d+)$', term, re.IGNORECASE):
            return True
        if re.match(r'^(M|NGC|IC|PGC|LDN|LBN|VDB)\s?(\d+)$', term, re.IGNORECASE):
            return True
        return False

    @staticmethod
    def prepare_search_value(search_value, match_type, only_search_in_titles_and_descriptions):
        """
        If only_search_in_titles_and_descriptions is True, match_type is ALL, and the query
        contains no quotation marks, then only wrap contiguous tokens in quotes if they form
        an astronomy catalog name. Otherwise, leave the tokens unchanged.

        For example:
          - "M 31" becomes '"M 31"'
          - "foo bar" remains "foo bar"
          - "foo M 31 bar" becomes 'foo "M 31" bar'
        """
        # Only modify if conditions are met.
        if not (
                only_search_in_titles_and_descriptions and match_type == MatchType.ALL.value and '"' not in search_value):
            return search_value

        tokens = search_value.split()
        new_tokens = []
        i = 0
        while i < len(tokens):
            if tokens[i].startswith('-'):
                new_tokens.append(tokens[i])
                i += 1
            else:
                # Attempt to combine current token with the next one if available.
                if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                    candidate = tokens[i] + " " + tokens[i + 1]
                    if EncodedSearchViewSet.is_astronomy_catalog(candidate):
                        new_tokens.append(f'"{candidate}"')
                        i += 2
                        continue
                # Otherwise, if the single token is an astro catalog (e.g. "NGC1234"),
                # leave it as is.
                if EncodedSearchViewSet.is_astronomy_catalog(tokens[i]):
                    new_tokens.append(tokens[i])
                else:
                    new_tokens.append(tokens[i])
                i += 1
        return " ".join(new_tokens)

    @staticmethod
    def split_include_exclude_terms(terms):
        """
        Splits a list of search query terms into inclusion and exclusion terms.

        Any term that starts with '-' is treated as an exclusion term (the leading '-' is removed),
        and all other terms are treated as inclusion terms.
        """
        include_terms = []
        exclude_terms = []
        for term in terms:
            if term.startswith('-'):
                exclude_terms.append(term[1:])
            else:
                include_terms.append(term)
        return include_terms, exclude_terms

    @staticmethod
    def expand_catalog_term(term):
        # Remove outer quotes if present (case-insensitive, no case conversion needed)
        if term and term[0] in ('"', "'") and term[-1] == term[0]:
            term = term[1:-1]

        # Sh2 catalog (case-insensitive)
        m = re.match(r'^(Sh2)[-\s]?(\d+)$', term, re.IGNORECASE)
        if m:
            prefix, number = m.groups()
            variant1 = f"{prefix}-{number}"
            variant2 = f"{prefix} {number}"
            return [variant1, variant2] if variant1 != variant2 else [variant1]

        # Other catalogs (case-insensitive)
        m = re.match(r'^(M|NGC|IC|PGC|LDN|LBN|VDB)\s?(\d+)$', term, re.IGNORECASE)
        if m:
            prefix, number = m.groups()
            variant1 = f"{prefix}{number}"
            variant2 = f"{prefix} {number}"
            return [variant1, variant2] if variant1 != variant2 else [variant1]

        return [term]

    @staticmethod
    def build_search_query(results, query, only_search_in_titles_and_descriptions=False):
        # Prepare the search value.
        search_value = query.get('value', '')
        match_type = query.get('matchType', MatchType.ANY.value)
        search_value = EncodedSearchViewSet.prepare_search_value(
            search_value, match_type, only_search_in_titles_and_descriptions
        )

        terms = EncodedSearchViewSet.parse_search_query(search_value)
        include_terms, exclude_terms = EncodedSearchViewSet.split_include_exclude_terms(terms)

        sqs = results
        search_fields = ['title', 'description'] if only_search_in_titles_and_descriptions else ['text']

        # Handle inclusion.
        if include_terms:
            q = None
            for term in include_terms:
                variants = EncodedSearchViewSet.expand_catalog_term(term)
                term_q = None
                for field in search_fields:
                    for variant in variants:
                        variant_value = EncodedSearchViewSet.prepare_search_value(
                            variant, match_type, only_search_in_titles_and_descriptions
                        )
                        q_variant = SQ(**{field: AutoQuery(variant_value)})
                        term_q = q_variant if term_q is None else term_q | q_variant
                if q is None:
                    q = term_q
                else:
                    if match_type == MatchType.ALL.value:
                        q &= term_q
                    else:
                        q |= term_q
            if q is not None:
                sqs = sqs.filter(q)

        # Handle exclusion: call exclude() for each exclusion term separately.
        for term in exclude_terms:
            variants = EncodedSearchViewSet.expand_catalog_term(term)
            term_exclusion_q = None
            for field in search_fields:
                for variant in variants:
                    variant_value = EncodedSearchViewSet.prepare_search_value(
                        variant, match_type, only_search_in_titles_and_descriptions
                    )
                    q_variant = SQ(**{field: AutoQuery(variant_value)})
                    term_exclusion_q = q_variant if term_exclusion_q is None else term_exclusion_q | q_variant
            if term_exclusion_q is not None:
                sqs = sqs.exclude(term_exclusion_q)

        return sqs

    def initialize_request(self, request, *args, **kwargs):
        def is_json(value):
            try:
                json_obj = json.loads(value)
                if isinstance(json_obj, (dict, list, bool, type(None))):
                    return True
                return False
            except json.JSONDecodeError:
                return False

        # Decode and decompress params before handling the request
        request = super().initialize_request(request, *args, **kwargs)
        params = request.query_params.get('params')
        if params:
            try:
                # Ensure correct Base64 padding
                padded_params = self.decode_base64_padding(unquote(params))
                # Base64 decode to get compressed data
                compressed_data = base64.b64decode(padded_params)
                # Decompress the data
                decompressed_data = zlib.decompress(compressed_data)
                # Decode the binary data back to a string
                query_string = msgpack.unpackb(decompressed_data, raw=False)
                # Parse the query string
                parsed_params = parse_qs(query_string)

                # Convert lists to single values if necessary
                decoded_params = self.simplify_one_item_lists(parsed_params)

                # Convert JSON strings back to objects where applicable
                for key, value in decoded_params.items():
                    if isinstance(value, str) and is_json(value):
                        try:
                            decoded_params[key] = json.loads(value)
                        except json.JSONDecodeError:
                            continue

                request = self.update_request_params(request, decoded_params)

            except (ValueError, TypeError, base64.binascii.Error, zlib.error) as e:
                raise ParseError(f"Error decoding parameters: {str(e)}")

        return request
