# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.parsers import BaseParser, DataAndFiles


class TusUploadStreamParser(BaseParser):
    media_type = 'application/offset+octet-stream'

    def parse(self, stream, media_type=None, parser_context=None):
        return DataAndFiles({'chunk': stream.body}, {})
