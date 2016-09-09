import unittest
from datetime import timedelta, datetime
from mock import patch, MagicMock
from pokemongo_bot.sleep_schedule import SleepSchedule
from tests import FakeBot


class FakeDatetime(datetime):
    def __new__(cls, *args, **kwargs):
        return datetime.__new__(datetime, *args, **kwargs)

class SleepScheduleTestCase(unittest.TestCase):
    config1 = { 'entries': [
                  {'time': '12:20', 'duration': '01:05', 'time_random_offset': '00:05', 'duration_random_offset': '00:05'},
                  {'time': '15:00', 'duration': '03:00', 'time_random_offset': '00:00', 'duration_random_offset': '00:00'},
                  {'time': '23:00', 'duration': '07:00', 'time_random_offset': '00:00', 'duration_random_offset': '00:00'}
                ]
              }

    config2 = { 'entries': [
                  {'time': '12:20', 'duration': '01:05', 'time_random_offset': '00:05', 'duration_random_offset': '00:05'}
                ]
              }

    def setUp(self):
        self.bot = MagicMock()
        self.worker1 = SleepSchedule(self.bot, self.config1)
        self.worker2 = SleepSchedule(self.bot, self.config2)
        self.bot.event_manager = MagicMock()
        self.bot.event_manager.emit = lambda *args, **kwargs: None

    def setNow(self, val):
        FakeDatetime.now = classmethod(lambda cls: val)

    def test_config(self):
        self.assertEqual(self.worker1.entries[0]['time'].hour, 12)
        self.assertEqual(self.worker1.entries[0]['time'].minute, 20)
        self.assertEqual(self.worker1.entries[0]['duration'], timedelta(hours=1, minutes=5).total_seconds())
        self.assertEqual(self.worker1.entries[0]['time_random_offset'], timedelta(minutes=5).total_seconds())
        self.assertEqual(self.worker1.entries[0]['duration_random_offset'], timedelta(minutes=5).total_seconds())

    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_get_next_time(self):
        self.setNow(datetime(year=2016, month=8, day=01, hour=8, minute=0))

        next_time = self.worker1._get_next_sleep_schedule()[0]
        from_date = datetime(year=2016, month=8, day=1, hour=12, minute=15)
        to_date = datetime(year=2016, month=8, day=1, hour=12, minute=25)

        self.assertGreaterEqual(next_time, from_date)
        self.assertLessEqual(next_time, to_date)

    @unittest.skipIf(SleepSchedule.SCHEDULING_MARGIN != timedelta(minutes=10), "Modifed SCHEDULING_MARGIN detected")
    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_get_next_time_called_near_activation_time(self):
        self.setNow(datetime(year=2016, month=8, day=01, hour=14, minute=51))

        next_time = self.worker1._get_next_sleep_schedule()[0]
        expected_start = datetime(year=2016, month=8, day=1, hour=23, minute=00)

        self.assertEqual(next_time, expected_start)

    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_get_next_time_called_before_activation_time(self):
        self.setNow(datetime(year=2016, month=8, day=1, hour=11, minute=25))

        next = self.worker1._get_next_sleep_schedule()[0]
        from_date = datetime(year=2016, month=8, day=01, hour=12, minute=15)
        to_date = datetime(year=2016, month=8, day=01, hour=12, minute=25)

        self.assertGreaterEqual(next, from_date)
        self.assertLessEqual(next, to_date)

    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_start_within_sleep_range(self):
        self.setNow(datetime(year=2016, month=8, day=1, hour=12, minute=25))

        sleep_now = self.worker1._get_next_sleep_schedule()[4]

        self.assertEqual(sleep_now, True)

    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_start_within_sleep_range_beginning_previous_day(self):
        self.setNow(datetime(year=2016, month=8, day=1, hour=02, minute=00))

        sleep_now = self.worker1._get_next_sleep_schedule()[4]

        self.assertEqual(sleep_now, True)

    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_get_next_time_called_within_sleep_range(self):
        self.setNow(datetime(year=2016, month=8, day=1, hour=16, minute=00))

        next, _, end_time, _, _ = self.worker1._get_next_sleep_schedule()
        expected_start = datetime(year=2016, month=8, day=1, hour=15, minute=00)
        expected_end = datetime(year=2016, month=8, day=1, hour=18, minute=00)

        self.assertEqual(next, expected_start)
        self.assertEqual(end_time, expected_end)

    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_get_next_time_called_when_this_days_time_passed(self):
        self.setNow(datetime(year=2016, month=8, day=1, hour=19, minute=0))

        next = self.worker2._get_next_sleep_schedule()[0]
        from_date = datetime(year=2016, month=8, day=02, hour=12, minute=15)
        to_date = datetime(year=2016, month=8, day=02, hour=12, minute=25)

        self.assertGreaterEqual(next, from_date)
        self.assertLessEqual(next, to_date)

    def test_get_next_duration(self):
        from_seconds = int(timedelta(hours=1).total_seconds())
        to_seconds = int(timedelta(hours=1, minutes=10).total_seconds())

        duration = self.worker1._get_next_duration(self.worker1.entries[0])

        self.assertGreaterEqual(duration, from_seconds)
        self.assertLessEqual(duration, to_seconds)

    @patch('pokemongo_bot.sleep_schedule.sleep')
    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_call_work_before_schedule(self, mock_sleep):
        self.worker1._next_sleep = datetime(year=2016, month=8, day=1, hour=12, minute=0)
        self.setNow(self.worker1._next_sleep - timedelta(minutes=5))

        self.worker1.work()

        self.assertEqual(mock_sleep.call_count, 0)

    @patch('pokemongo_bot.sleep_schedule.sleep')
    @patch('pokemongo_bot.sleep_schedule.datetime', FakeDatetime)
    def test_call_work_after_schedule(self, mock_sleep):
        self.bot.login = MagicMock()
        self.worker1._next_sleep = datetime(year=2016, month=8, day=1, hour=12, minute=0)
        # Change time to be after schedule
        self.setNow(self.worker1._next_sleep + timedelta(minutes=5))

        self.worker1.work()

        self.assertGreater(mock_sleep.call_count, 0)
        self.assertGreater(self.bot.login.call_count, 0)
