from django.test import TestCase

from common.services import DateTimeService


class DateTimeServiceTest(TestCase):
    def test_human_time_duration(self):
        self.assertEqual('0&Prime;', DateTimeService.human_time_duration(None))
        self.assertEqual('0&Prime;', DateTimeService.human_time_duration(0))
        self.assertEqual('1&prime;', DateTimeService.human_time_duration(60))
        self.assertEqual('1h', DateTimeService.human_time_duration(60 * 60))
        self.assertEqual('10h', DateTimeService.human_time_duration(60 * 60 * 10))
        self.assertEqual('1h 1&prime;', DateTimeService.human_time_duration(60 * 60 + 60))
        self.assertEqual('1h 1&prime; 1&Prime;', DateTimeService.human_time_duration(60 * 60 + 60 + 1))
        self.assertEqual('1h 1&prime; 1&Prime; .1', DateTimeService.human_time_duration(60 * 60 + 60 + 1.1))
        self.assertEqual('25h', DateTimeService.human_time_duration(25 * 60 * 60))
        self.assertEqual('0.25&Prime;', DateTimeService.human_time_duration(.25))
