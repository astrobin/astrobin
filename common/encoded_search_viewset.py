import base64
import json
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
    def build_search_query(results, query, only_search_in_titles_and_descriptions=False):
        search_value = query.get('value', '')
        match_type = query.get('matchType', MatchType.ANY.value)

        terms = EncodedSearchViewSet.parse_search_query(search_value)

        # Split into include and exclude terms
        include_terms = [term[1:] if term.startswith('"') and term.startswith('-', 1) else term
                         for term in terms if not term.startswith('-') or term.startswith('-"')]
        exclude_terms = [term[1:] for term in terms if term.startswith('-')]

        sqs = results

        # Determine which fields to search
        search_fields = ['title', 'description'] if only_search_in_titles_and_descriptions else ['text']

        # Handle inclusion
        if include_terms:
            q = None
            for term in include_terms:
                term_q = None
                for field in search_fields:
                    if term_q is None:
                        term_q = SQ(**{field: AutoQuery(term)})
                    else:
                        term_q |= SQ(**{field: AutoQuery(term)})

                if match_type == MatchType.ALL.value:
                    if q is None:
                        q = term_q
                    else:
                        q &= term_q
                else:  # ANY
                    if q is None:
                        q = term_q
                    else:
                        q |= term_q

            if q is not None:
                sqs = sqs.filter(q)

        # Handle exclusion - always use AND NOT for each field
        for term in exclude_terms:
            exclude_q = None
            for field in search_fields:
                if exclude_q is None:
                    exclude_q = SQ(**{field: AutoQuery(term)})
                else:
                    exclude_q |= SQ(**{field: AutoQuery(term)})
            sqs = sqs.exclude(exclude_q)

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
