import unittest, pickle, os
import requests_mock
from mock import patch, Mock
from pokemongo_bot.walkers.polyline_generator import Polyline
import datetime
import time

mock_start, mock_seven_sec, mock_end = Mock(), Mock(), Mock()
mock_start.return_value = time.mktime(datetime.datetime(2016, 8, 20).timetuple())
mock_seven_sec.return_value = time.mktime(datetime.datetime(2016, 8, 20, 0 , 0, 7).timetuple())
mock_end.return_value = time.mktime(datetime.datetime(2016, 8, 21).timetuple())

ex_orig = (47.1706378, 8.5167405)
ex_dest = (47.1700271, 8.518072999999998)
ex_speed = 2.5
ex_total_distance = 194
ex_resp_directions = 'example_directions.pickle'
ex_resp_elevations = 'example_elevations.pickle'
ex_enc_polyline = 'o_|~Gsl~r@??h@LVDf@LDcBFi@AUEUQg@EKCI?G?GBG@EBEJKNC??'
ex_nr_samples = 78



class PolylineTestCase(unittest.TestCase):
    @patch('time.time', mock_start)
    def setUp(self):
        directions_path = os.path.join(os.path.dirname(__file__), 'resources', ex_resp_directions)
        with open(directions_path, 'rb') as directions:
            ex_directions = pickle.load(directions)
        elevations_path = os.path.join(os.path.dirname(__file__), 'resources', ex_resp_elevations)
        with open(elevations_path, 'rb') as elevations:
            ex_elevations = pickle.load(elevations)
        with requests_mock.Mocker() as m:
            m.get('https://maps.googleapis.com/maps/api/directions/json?mode=walking&origin={},{}&destination={},{}'.format(
                ex_orig[0], ex_orig[1], ex_dest[0], ex_dest[1]
            ), json=ex_directions, status_code=200)
            m.get('https://maps.googleapis.com/maps/api/elevation/json?path=enc:{}&samples={}'.format(
                ex_enc_polyline, ex_nr_samples
            ), json=ex_elevations, status_code=200)
            self.polyline = Polyline(ex_orig, ex_dest, ex_speed)

    @patch('time.time', mock_start)
    def test_reset_timestamps(self):
        timestamp = self.polyline._timestamp
        is_paused = self.polyline.is_paused
        last_pause = self.polyline._last_paused_timestamp
        total_pause = self.polyline._paused_total
        self.polyline.pause()
        @patch('time.time', mock_seven_sec)
        def unpause():
            self.polyline.unpause()
        unpause()
        self.polyline.reset_timestamps()
        self.assertEquals(timestamp, self.polyline._timestamp)
        self.assertEquals(is_paused, self.polyline.is_paused)
        self.assertEquals(last_pause, self.polyline._last_paused_timestamp)
        self.assertEquals(total_pause, self.polyline._paused_total)

    def test_walk_step_no_points(self):
        self.assertEquals(self.polyline.walk_steps(None), [])
        self.assertEquals(self.polyline.walk_steps([]), [])

    def test_first_point(self):
        self.assertEqual(self.polyline.points[0], ex_orig)

    def test_last_point(self):
        self.assertEqual(self.polyline.points[-1], ex_dest)

    @patch('time.time', mock_start)
    def test_pos_and_alt_at_time_mock_start(self):
        self.assertEquals(self.polyline.get_pos(), (round(ex_orig[0], 5), round(ex_orig[1], 5)))
        self.assertEquals(self.polyline.get_alt(), round(self.polyline.polyline_elevations[0], 2))

    @patch('time.time', mock_seven_sec)
    def test_pos_and_alt_at_time_mock_seven_sec(self):
        self.assertEquals(self.polyline.get_pos(), (47.17049, 8.51669))
        self.assertAlmostEqual(self.polyline.get_alt(), self.polyline.polyline_elevations[6], places=2)

    @patch('time.time', mock_end)
    def test_pos_and_alt_at_time_mock_end(self):
        self.assertEquals(self.polyline.get_pos(), ex_dest)
        self.assertAlmostEqual(self.polyline.get_alt(), self.polyline.polyline_elevations[-1], places=2)

    def test_nr_of_elevations_returned(self):
        total_seconds = self.polyline.get_total_distance(self.polyline.points)/self.polyline.speed
        self.assertAlmostEqual(total_seconds, ex_nr_samples, places=0)

    def test_conversion_factor(self):
        self.polyline.speed = 0.0001
        self.polyline.polyline_elevations = [100]*512
        self.assertEquals(self.polyline.get_alt(), 100)

    def test_no_points(self):
        self.polyline.points = [ex_orig]
        self.assertEquals(self.polyline.get_pos(), ex_orig)
        self.polyline.points = [ex_dest]
        self.assertEquals(self.polyline.get_pos(), ex_dest)

    def test_pause(self):
        self.assertEquals(self.polyline._last_paused_timestamp, None)
        @patch('time.time', mock_start)
        def pause():
            self.polyline.pause()
            self.assertEquals(self.polyline.is_paused, True)
            self.assertEquals(self.polyline._last_paused_timestamp, time.time())
        pause()

        @patch('time.time', mock_seven_sec)
        def position_check():
            self.assertEquals(self.polyline.get_pos(), (round(ex_orig[0], 5), round(ex_orig[1], 5)))
            self.assertEquals(self.polyline.get_alt(), round(self.polyline.polyline_elevations[0], 2))
        position_check()

    def test_unpause(self):
        @patch('time.time', mock_start)
        def pause():
            self.polyline.pause()
        pause()
        self.assertEquals(self.polyline.is_paused, True)
        @patch('time.time', mock_seven_sec)
        def unpause():
            self.polyline.unpause()
        unpause()
        self.assertEquals(self.polyline.is_paused, False)
        self.assertEquals(self.polyline._last_paused_timestamp, None)
        self.assertEquals(self.polyline._paused_total, 7)

        @patch('time.time', mock_seven_sec)
        def position_check():
            self.assertEquals(self.polyline.get_pos(), (round(ex_orig[0], 5), round(ex_orig[1], 5)))
            self.assertEquals(self.polyline.get_alt(), round(self.polyline.polyline_elevations[0], 2))
        position_check()

    def test_total_distance(self):
        self.assertEquals(self.polyline.get_total_distance(self.polyline.points), ex_total_distance)

    def test_get_last_pos(self):
        self.assertEquals(self.polyline.get_last_pos(), self.polyline._last_pos)

