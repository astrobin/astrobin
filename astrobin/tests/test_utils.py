from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from mock import patch

from astrobin import utils
from astrobin.tests.generators import Generators
from astrobin.utils import (
    add_url_params, dec_decimal_precision_from_pixel_scale, decimal_to_degrees_minutes_seconds_string,
    decimal_to_hours_minutes_seconds_string,
    ra_decimal_precision_from_pixel_scale,
)


class UtilsTest(TestCase):
    @patch("astrobin.utils.get_client_ip")
    @patch("django.contrib.gis.geoip2.GeoIP2.country_code")
    def test_get_client_country_code(self, mock_country, mock_get_client_ip):
        mock_country.return_value = "CH"
        mock_get_client_ip.return_value = "123.123.123.123"

        self.assertEqual("CH", utils.get_client_country_code(None))

    def test_never_activated_accounts_no_users(self):
        self.assertEqual(0, utils.never_activated_accounts().count())

    def test_never_activated_accounts_none_found_too_recent(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(1)
        u.save()

        accounts = utils.never_activated_accounts()

        self.assertEqual(0, accounts.count())

    def test_never_activated_accounts_none_found_already_activated(self):
        u = Generators.user()
        u.is_active = True
        u.date_joined = timezone.now() - timedelta(15)
        u.save()

        accounts = utils.never_activated_accounts()

        self.assertEqual(0, accounts.count())

    def test_never_activated_accounts_none_found_already_sent_reminder(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(15)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.save()

        accounts = utils.never_activated_accounts()

        self.assertEqual(0, accounts.count())

    def test_never_activated_accounts_one_found(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(15)
        u.save()

        accounts = utils.never_activated_accounts()

        self.assertEqual(1, accounts.count())
        self.assertEqual(u, accounts.first())

    def test_never_activated_accounts_two_found(self):
        first = Generators.user()
        first.is_active = False
        first.date_joined = timezone.now() - timedelta(15)
        first.save()

        second = Generators.user()
        second.is_active = False
        second.date_joined = timezone.now() - timedelta(15)
        second.save()

        accounts = utils.never_activated_accounts()

        self.assertEqual(2, accounts.count())

    def test_never_activated_accounts_to_be_deleted_no_users(self):
        self.assertEqual(0, utils.never_activated_accounts_to_be_deleted().count())

    def test_never_activated_accounts_to_be_deleted_none_found_too_recent(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(20)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEqual(0, accounts.count())

    def test_never_activated_accounts_to_be_deleted_none_found_already_activated(self):
        u = Generators.user()
        u.is_active = True
        u.date_joined = timezone.now() - timedelta(22)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEqual(0, accounts.count())

    def test_never_activated_accounts_to_be_deleted_none_does_not_have_already_sent_reminder(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(22)
        u.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEqual(0, accounts.count())

    def test_never_activated_accounts_to_be_deleted_userprofile_deleted(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(22)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.delete()
        u.userprofile.save(keep_deleted=True)

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEqual(0, accounts.count())

    def test_never_activated_accounts_to_be_deleted_one_found(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(22)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEqual(1, accounts.count())
        self.assertEqual(u, accounts.first())

    def test_never_activated_accounts_to_be_deleted_two_found(self):
        first = Generators.user()
        first.is_active = False
        first.date_joined = timezone.now() - timedelta(22)
        first.save()

        first.userprofile.never_activated_account_reminder_sent = timezone.now()
        first.userprofile.save()

        second = Generators.user()
        second.is_active = False
        second.date_joined = timezone.now() - timedelta(22)
        second.save()

        second.userprofile.never_activated_account_reminder_sent = timezone.now()
        second.userprofile.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEqual(2, accounts.count())

    def test_unique_items(self):
        list_with_duplicates = ['foo', 'bar', 'baz', 'foo', '2', '6', '10', '2']
        expected_result = ['foo', 'bar', 'baz', '2', '6', '10']

        self.assertEqual(sorted(expected_result), sorted(utils.unique_items(list_with_duplicates)))

    def test_unique_items_list_not_flat(self):
        list_with_duplicates = ['foo', 'bar', 'baz', 'foo',
                                '2', ['b', 'c', 'a'], '6', '10', '2', ['b', 'c', 'a']]
        expected_result = ['foo', 'bar', 'baz', '2', ['b', 'c', 'a'], '6', '10']

        self.assertEqual(expected_result, utils.unique_items(list_with_duplicates))

    def test_number_unit_decimals(self):
        self.assertEquals('10h', utils.number_unit_decimals(10, 'h', 0))
        self.assertEquals('10h.00', utils.number_unit_decimals(10, 'h', 2))
        self.assertEquals('10h.123', utils.number_unit_decimals(10.123, 'h', 3))
        self.assertEquals('10h.1230', utils.number_unit_decimals(10.123, 'h', 4))

    def test_number_unit_decimals_html(self):
        self.assertEquals('10<span class="symbol">h</span>', utils.number_unit_decimals_html(10, 'h', 0))
        self.assertEquals('10<span class="symbol">h</span>.00', utils.number_unit_decimals_html(10, 'h', 2))
        self.assertEquals('10<span class="symbol">h</span>.123', utils.number_unit_decimals_html(10.123, 'h', 3))
        self.assertEquals('10<span class="symbol">h</span>.1230', utils.number_unit_decimals_html(10.123, 'h', 4))

    def test_dec_decimal_precision_from_pixel_scale(self):
        self.assertEqual(0, dec_decimal_precision_from_pixel_scale(0))
        self.assertEqual(0, dec_decimal_precision_from_pixel_scale(11))
        self.assertEqual(1, dec_decimal_precision_from_pixel_scale(10))
        self.assertEqual(1, dec_decimal_precision_from_pixel_scale(9))
        self.assertEqual(1, dec_decimal_precision_from_pixel_scale(1.1))
        self.assertEqual(2, dec_decimal_precision_from_pixel_scale(1))
        self.assertEqual(2, dec_decimal_precision_from_pixel_scale(.1))

    def test_ra_decimal_precision_from_pixel_scale(self):
        self.assertEqual(1, ra_decimal_precision_from_pixel_scale(0))
        self.assertEqual(1, ra_decimal_precision_from_pixel_scale(100))
        self.assertEqual(2, ra_decimal_precision_from_pixel_scale(10))
        self.assertEqual(2, ra_decimal_precision_from_pixel_scale(9))
        self.assertEqual(2, ra_decimal_precision_from_pixel_scale(1.1))
        self.assertEqual(3, ra_decimal_precision_from_pixel_scale(1))
        self.assertEqual(3, ra_decimal_precision_from_pixel_scale(.1))

    def test_decimal_to_hours_minutes_seconds_string_avoid_60_seconds(self):
        self.assertEqual(
            '20 51 59',
            decimal_to_hours_minutes_seconds_string(
                312.998,
                hour_symbol='',
                minute_symbol='',
                second_symbol='',
            )
        )

    def test_decimal_to_degrees_minutes_seconds_string_avoid_60_seconds(self):
        self.assertEqual(
            '+3 25 59',
            decimal_to_degrees_minutes_seconds_string(
                3.433272140,
                degree_symbol='',
                minute_symbol='',
                second_symbol='',
            )
        )

    def test_add_new_params(self):
        url = "https://example.com/"
        params = {'key1': 'value1'}
        new_url = add_url_params(url, params)
        self.assertEqual(new_url, "https://example.com/?key1=value1")

    def test_add_new_params_update_existing_param(self):
        url = "https://example.com/?key1=oldvalue1"
        params = {'key1': 'newvalue1'}
        new_url = add_url_params(url, params)
        self.assertEqual(new_url, "https://example.com/?key1=newvalue1")

    def test_add_new_params_add_multiple_params(self):
        url = "https://example.com/"
        params = {'key1': 'value1', 'key2': 'value2'}
        new_url = add_url_params(url, params)
        # Order of query parameters may vary
        self.assertIn(
            new_url, ["https://example.com/?key1=value1&key2=value2", "https://example.com/?key2=value2&key1=value1"]
        )

    def test_add_new_params_update_and_add_params(self):
        url = "https://example.com/?key1=oldvalue1"
        params = {'key1': 'newvalue1', 'key2': 'value2'}
        new_url = add_url_params(url, params)
        # Order of query parameters may vary
        self.assertIn(
            new_url,
            ["https://example.com/?key1=newvalue1&key2=value2", "https://example.com/?key2=value2&key1=newvalue1"]
        )

    def test_add_new_params_no_params_given(self):
        url = "https://example.com/"
        params = {}
        new_url = add_url_params(url, params)
        self.assertEqual(new_url, "https://example.com/")

    def test_add_new_params_preserve_other_url_parts(self):
        url = "https://example.com:8080/path/?key1=oldvalue1#fragment"
        params = {'key1': 'newvalue1', 'key2': 'value2'}
        new_url = add_url_params(url, params)
        self.assertEqual(new_url, "https://example.com:8080/path/?key1=newvalue1&key2=value2#fragment")
