import base64
import json
import re
import zlib
from urllib.parse import parse_qs, unquote

import msgpack
from drf_haystack.viewsets import HaystackViewSet
from haystack.backends import SQ
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
        # This regex will match phrases wrapped in single or double quotes and individual words
        pattern = r'(-?"[^"]+"|-?\'[^\']+\'|-?\S+)'
        terms = re.findall(pattern, query)

        include_terms = []
        exclude_terms = []

        for term in terms:
            if term.startswith('-'):
                exclude_terms.append(term[1:].strip('\'"'))
            else:
                include_terms.append(term.strip('\'"'))

        return include_terms, exclude_terms

    @staticmethod
    def build_search_query(results, query):
        include_terms, exclude_terms = EncodedSearchViewSet.parse_search_query(query.get('value', ''))
        match_type = query.get('matchType', MatchType.ANY.value)
        search_query = SQ()

        # Handle included terms (AND logic or OR logic depending on matchType)
        for term in include_terms:
            if match_type == MatchType.ALL.value:
                search_query &= SQ(text=term)
            else:
                search_query |= SQ(text=term)

        # Handle excluded terms (NOT logic)
        for term in exclude_terms:
            if match_type == MatchType.ALL.value:
                search_query &= ~SQ(text=term)
            else:
                search_query |= ~SQ(text=term)

        return results.filter(search_query)

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
