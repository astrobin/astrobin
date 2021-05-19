from django.test import TestCase

from common.services import DateTimeService


class DateTimeServiceTest(TestCase):
    def test_human_time_duration(self):
        self.assertEquals('0', DateTimeService.human_time_duration(None))
        self.assertEquals('0', DateTimeService.human_time_duration(0))
        self.assertEquals('1\'', DateTimeService.human_time_duration(60))
        self.assertEquals('1h', DateTimeService.human_time_duration(60 * 60))
        self.assertEquals('1h 1\'', DateTimeService.human_time_duration(60 * 60 + 60))
        self.assertEquals('1h 1\' 1"', DateTimeService.human_time_duration(60 * 60 + 60 + 1))
        self.assertEquals('25h', DateTimeService.human_time_duration(25 * 60 * 60))
