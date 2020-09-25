from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from mock import patch

from astrobin import utils
from astrobin.tests.generators import Generators


class UtilsTest(TestCase):
    @patch("astrobin.utils.get_client_ip")
    @patch("django.contrib.gis.geoip2.GeoIP2.country_code")
    def test_get_client_country_code(self, mock_country, mock_get_client_ip):
        mock_country.return_value = "CH"
        mock_get_client_ip.return_value = "123.123.123.123"

        self.assertEquals("CH", utils.get_client_country_code(None))

    def test_never_activated_accounts_no_users(self):
        self.assertEquals(0, utils.never_activated_accounts().count())

    def test_never_activated_accounts_none_found_too_recent(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(1)
        u.save()

        accounts = utils.never_activated_accounts()

        self.assertEquals(0, accounts.count())

    def test_never_activated_accounts_none_found_already_activated(self):
        u = Generators.user()
        u.is_active = True
        u.date_joined = timezone.now() - timedelta(15)
        u.save()

        accounts = utils.never_activated_accounts()

        self.assertEquals(0, accounts.count())

    def test_never_activated_accounts_none_found_already_sent_reminder(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(15)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.save()

        accounts = utils.never_activated_accounts()

        self.assertEquals(0, accounts.count())

    def test_never_activated_accounts_one_found(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(15)
        u.save()

        accounts = utils.never_activated_accounts()

        self.assertEquals(1, accounts.count())
        self.assertEquals(u, accounts.first())

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

        self.assertEquals(2, accounts.count())

    def test_never_activated_accounts_to_be_deleted_no_users(self):
        self.assertEquals(0, utils.never_activated_accounts_to_be_deleted().count())

    def test_never_activated_accounts_to_be_deleted_none_found_too_recent(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(20)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEquals(0, accounts.count())

    def test_never_activated_accounts_to_be_deleted_none_found_already_activated(self):
        u = Generators.user()
        u.is_active = True
        u.date_joined = timezone.now() - timedelta(22)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEquals(0, accounts.count())

    def test_never_activated_accounts_to_be_deleted_none_does_not_have_already_sent_reminder(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(22)
        u.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEquals(0, accounts.count())

    def test_never_activated_accounts_to_be_deleted_one_found(self):
        u = Generators.user()
        u.is_active = False
        u.date_joined = timezone.now() - timedelta(22)
        u.save()

        u.userprofile.never_activated_account_reminder_sent = timezone.now()
        u.userprofile.save()

        accounts = utils.never_activated_accounts_to_be_deleted()

        self.assertEquals(1, accounts.count())
        self.assertEquals(u, accounts.first())

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

        self.assertEquals(2, accounts.count())
