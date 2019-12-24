# -*- coding: utf-8 -*-

from django.test import TestCase

from astrobin.forms.utils import parseKeyValueTags


class FormUtilsTest(TestCase):
    def test_parse_key_value_tags_empty_tags(self):
        self.assertEqual([], parseKeyValueTags(""))

    def test_parse_key_value_tags_none_tags(self):
        self.assertEqual([], parseKeyValueTags(None))

    def test_parse_key_value_tags_missing_key(self):
        with self.assertRaises(ValueError):
            parseKeyValueTags("=a")

    def test_parse_key_value_tags_missing_value(self):
        with self.assertRaises(ValueError):
            parseKeyValueTags("a=")

    def test_parse_key_value_tags_missing_key_and_value(self):
        with self.assertRaises(ValueError):
            parseKeyValueTags("=")

    def test_parse_key_value_tags_duplicate_key(self):
        with self.assertRaises(ValueError):
            parseKeyValueTags("a=1\na=2")

    def test_parse_key_value_tags_double_equals(self):
        with self.assertRaises(ValueError):
            parseKeyValueTags("a==1")

    def test_parse_key_value_tags_two_equals(self):
        with self.assertRaises(ValueError):
            parseKeyValueTags("a=1=2")

    def test_parse_key_value_tags_success(self):
        self.assertEqual([{"key": "a", "value": "1"}], parseKeyValueTags("a=1"))

    def test_parse_key_value_tags_success_number_key(self):
        self.assertEqual([{"key": "2", "value": "1"}], parseKeyValueTags("2=1"))

    def test_parse_key_value_tags_success_non_ascii(self):
        self.assertEqual([{"key": "你好", "value": "再见"}], parseKeyValueTags("你好=再见"))

    def test_parse_key_value_tags_success_multiple(self):
        self.assertEqual([{"key": "a", "value": "1"}, {"key": "b", "value": "2"}], parseKeyValueTags("a=1\nb=2"))

    def test_parse_key_value_tags_success_multiple_rn(self):
        self.assertEqual([{"key": "a", "value": "1"}, {"key": "b", "value": "2"}], parseKeyValueTags("a=1\r\nb=2"))
