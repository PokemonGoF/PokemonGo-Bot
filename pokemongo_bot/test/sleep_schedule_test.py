import unittest
from datetime import timedelta, datetime
from mock import patch, MagicMock
from pokemongo_bot.cell_workers.sleep_schedule import SleepSchedule
from tests import FakeBot


class SleepScheculeTestCase(unittest.TestCase):
    config = {'time': '12:20', 'duration': '01:05', 'time_random_offset': '00:05', 'duration_random_offset': '00:05'}

    def setUp(self):
        self.bot = FakeBot()
        self.worker = SleepSchedule(self.bot, self.config)

    def test_config(self):
        self.assertEqual(self.worker.time.hour, 12)
        self.assertEqual(self.worker.time.minute, 20)
        self.assertEqual(self.worker.duration, timedelta(hours=1, minutes=5).total_seconds())
        self.assertEqual(self.worker.time_random_offset, timedelta(minutes=5).total_seconds())
        self.assertEqual(self.worker.duration_random_offset, timedelta(minutes=5).total_seconds())

    @patch('pokemongo_bot.cell_workers.sleep_schedule.datetime')
    def test_get_next_time(self, mock_datetime):
        mock_datetime.now.return_value = datetime(year=2016, month=8, day=01, hour=8, minute=0)

        next_time = self.worker._get_next_sleep_schedule()
        from_date = datetime(year=2016, month=8, day=1, hour=12, minute=15)
        to_date = datetime(year=2016, month=8, day=1, hour=12, minute=25)

        self.assertGreaterEqual(next_time, from_date)
        self.assertLessEqual(next_time, to_date)

    @patch('pokemongo_bot.cell_workers.sleep_schedule.datetime')
    def test_get_next_time_called_near_activation_time(self, mock_datetime):
        mock_datetime.now.return_value = datetime(year=2016, month=8, day=1, hour=12, minute=25)

        next = self.worker._get_next_sleep_schedule()
        from_date = datetime(year=2016, month=8, day=02, hour=12, minute=15)
        to_date = datetime(year=2016, month=8, day=02, hour=12, minute=25)

        self.assertGreaterEqual(next, from_date)
        self.assertLessEqual(next, to_date)

    @patch('pokemongo_bot.cell_workers.sleep_schedule.datetime')
    def test_get_next_time_called_when_this_days_time_passed(self, mock_datetime):
        mock_datetime.now.return_value = datetime(year=2016, month=8, day=1, hour=14, minute=0)

        next = self.worker._get_next_sleep_schedule()
        from_date = datetime(year=2016, month=8, day=02, hour=12, minute=15)
        to_date = datetime(year=2016, month=8, day=02, hour=12, minute=25)

        self.assertGreaterEqual(next, from_date)
        self.assertLessEqual(next, to_date)

    def test_get_next_duration(self):
        from_seconds = int(timedelta(hours=1).total_seconds())
        to_seconds = int(timedelta(hours=1, minutes=10).total_seconds())

        duration = self.worker._get_next_duration()

        self.assertGreaterEqual(duration, from_seconds)
        self.assertLessEqual(duration, to_seconds)

    @patch('pokemongo_bot.cell_workers.sleep_schedule.sleep')
    def test_sleep(self, mock_sleep):
        self.worker._next_duration = SleepSchedule.LOG_INTERVAL_SECONDS * 10
        self.worker._sleep()
        #Sleep should be  called 10 times with LOG_INTERVAL_SECONDS as argument
        self.assertEqual(mock_sleep.call_count, 10)
        calls = [x[0][0] for x in mock_sleep.call_args_list]
        for arg in calls:
            self.assertEqual(arg, SleepSchedule.LOG_INTERVAL_SECONDS)

    @patch('pokemongo_bot.cell_workers.sleep_schedule.sleep')
    def test_sleep_not_divedable_by_interval(self, mock_sleep):
        self.worker._next_duration = SleepSchedule.LOG_INTERVAL_SECONDS * 10 + 5
        self.worker._sleep()
        self.assertEqual(mock_sleep.call_count, 11)

        calls = [x[0][0] for x in mock_sleep.call_args_list]
        for arg in calls[:-1]:
            self.assertEqual(arg, SleepSchedule.LOG_INTERVAL_SECONDS)
        #Last call must be 5
        self.assertEqual(calls[-1], 5)

    @patch('pokemongo_bot.cell_workers.sleep_schedule.sleep')
    @patch('pokemongo_bot.cell_workers.sleep_schedule.datetime')
    def test_call_work_before_schedule(self, mock_datetime, mock_sleep):
        self.worker._next_sleep = datetime(year=2016, month=8, day=1, hour=12, minute=0)
        mock_datetime.now.return_value = self.worker._next_sleep - timedelta(minutes=5)

        self.worker.work()

        self.assertEqual(mock_sleep.call_count, 0)

    @patch('pokemongo_bot.cell_workers.sleep_schedule.sleep')
    @patch('pokemongo_bot.cell_workers.sleep_schedule.datetime')
    def test_call_work_after_schedule(self, mock_datetime, mock_sleep):
        self.bot.login = MagicMock()
        self.worker._next_sleep = datetime(year=2016, month=8, day=1, hour=12, minute=0)
        # Change time to be after schedule
        mock_datetime.now.return_value = self.worker._next_sleep + timedelta(minutes=5)

        self.worker.work()

        self.assertGreater(mock_sleep.call_count, 0)
        self.assertGreater(self.bot.login.call_count, 0)
