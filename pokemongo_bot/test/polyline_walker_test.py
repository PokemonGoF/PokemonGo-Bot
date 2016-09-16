import os
import pickle
import unittest

from geographiclib.geodesic import Geodesic
from mock import MagicMock, patch, mock

import requests_mock
from pokemongo_bot.walkers.polyline_generator import PolylineObjectHandler
from pokemongo_bot.walkers.polyline_walker import PolylineWalker


ex_orig = (47.1706378, 8.5167405)
ex_dest = (47.1700271, 8.518072999999998)
ex_speed = 2.5
ex_total_distance = 194
ex_resp_directions = 'example_directions.pickle'
ex_resp_elevations = 'example_elevations.pickle'
ex_enc_polyline = 'o_%7C~Gsl~r@??h@LVDf@LDcBFi@AUEUQg@EKCI?G?GBG@EBEJKNC??'
ex_nr_samples = 64


class TestPolylineWalker(unittest.TestCase):
    def setUp(self):
        self.patcherSleep = patch('pokemongo_bot.walkers.step_walker.sleep')
        self.patcherSleep.start()

        self.bot = MagicMock()
        self.bot.api = MagicMock()

        # let us get back the position set by the PolylineWalker
        def api_set_position(lat, lng, alt):
            self.bot.position = [lat, lng, alt]

        def hearbeat():
            return True

        self.bot.config.gmapkey = ''
        self.bot.api.set_position = api_set_position
        self.bot.heartbeat = hearbeat

        directions_path = os.path.join(os.path.dirname(__file__), 'resources', ex_resp_directions)
        with open(directions_path, 'rb') as directions:
            ex_directions = pickle.load(directions)
        elevations_path = os.path.join(os.path.dirname(__file__), 'resources', ex_resp_elevations)
        with open(elevations_path, 'rb') as elevations:
            ex_elevations = pickle.load(elevations)
        with requests_mock.Mocker() as m:
            m.get(
                "https://maps.googleapis.com/maps/api/directions/json?mode=walking&origin={},{}&destination={},{}".format(
                    ex_orig[0], ex_orig[1], ex_dest[0], ex_dest[1]
                ), json=ex_directions, status_code=200)
            m.get("https://maps.googleapis.com/maps/api/elevation/json?path=enc:{}&samples={}".format(
                ex_enc_polyline, ex_nr_samples
            ), json=ex_elevations, status_code=200)
            self.polyline = PolylineObjectHandler.cached_polyline(ex_orig, ex_dest)

        self.bot.position = [ex_orig[0], ex_orig[1], self.polyline.get_alt(ex_orig)]

    def tearDown(self):
        self.bot.position = [0, 0, 0]
        self.patcherSleep.stop()

    def test_polyline_fetched(self):
        self.assertEqual(self.polyline._points[0], ex_orig)
        self.assertEqual(self.polyline._points[-1], ex_dest)
        total_seconds = self.polyline.get_total_distance() / 3
        self.assertAlmostEqual(total_seconds, ex_nr_samples, places=0)
        self.assertEquals(self.polyline.get_total_distance(), ex_total_distance)
        self.assertEquals(self.polyline.get_last_pos(), self.polyline._last_pos)

    def test_one_small_speed(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min
        speed = 0.247503233266
        precision = 0.0
        dlat = 47.17064
        dlng = 8.51674

        self.bot.config.walk_max = speed
        self.bot.config.walk_min = speed

        pw = PolylineWalker(self.bot, ex_dest[0], ex_dest[1], precision=precision)
        self.assertEqual(pw.dest_lat, ex_dest[0], 'dest_lat did not match')
        self.assertEqual(pw.dest_lng, ex_dest[1], 'dest_lng did not match')

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return pw.step()

        finishedWalking = run_step()
        self.assertFalse(finishedWalking, 'step should return False')

        distance = Geodesic.WGS84.Inverse(dlat, dlng, self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (pw.precision + pw.epsilon))
        self.polyline._last_pos = (dlat, dlng)
        self.assertTrue(abs(self.polyline.get_alt() - self.bot.position[2]) <= 1)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_one_small_speed_big_precision(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min
        speed = 0.247503233266
        precision = 2.5
        dlat = 47.170635631
        dlng = 8.51673976413

        self.bot.config.walk_max = speed
        self.bot.config.walk_min = speed

        pw = PolylineWalker(self.bot, ex_dest[0], ex_dest[1], precision=precision)
        self.assertEqual(pw.dest_lat, ex_dest[0], 'dest_lat did not match')
        self.assertEqual(pw.dest_lng, ex_dest[1], 'dest_lng did not match')

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return pw.step()

        finishedWalking = run_step()
        self.assertFalse(finishedWalking, 'step should return False')

        distance = Geodesic.WGS84.Inverse(dlat, dlng, self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (pw.precision + pw.epsilon))
        self.polyline._last_pos = (dlat, dlng)
        self.assertTrue(abs(self.polyline.get_alt() - self.bot.position[2]) <= 1)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_intermediary_speed(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min
        speed = 166.8285172348795
        precision = 0.0
        dlat = 47.17022
        dlng = 8.51789

        self.bot.config.walk_max = speed
        self.bot.config.walk_min = speed

        pw = PolylineWalker(self.bot, ex_dest[0], ex_dest[1], precision=precision)
        self.assertEqual(pw.dest_lat, ex_dest[0], 'dest_lat did not match')
        self.assertEqual(pw.dest_lng, ex_dest[1], 'dest_lng did not match')

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return pw.step()

        finishedWalking = run_step()
        self.assertFalse(finishedWalking, 'step should return False')

        distance = Geodesic.WGS84.Inverse(dlat, dlng, self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (pw.precision + pw.epsilon))
        self.polyline._last_pos = (dlat, dlng)
        self.assertTrue(abs(self.polyline.get_alt() - self.bot.position[2]) <= 1)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_intermediary_speed_big_precision(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min
        speed = 166.8285172348795
        precision = 2.5
        dlat = 47.17022
        dlng = 8.51789

        self.bot.config.walk_max = speed
        self.bot.config.walk_min = speed

        pw = PolylineWalker(self.bot, ex_dest[0], ex_dest[1], precision=precision)
        self.assertEqual(pw.dest_lat, ex_dest[0], 'dest_lat did not match')
        self.assertEqual(pw.dest_lng, ex_dest[1], 'dest_lng did not match')

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return pw.step()

        finishedWalking = run_step()
        self.assertFalse(finishedWalking, 'step should return False')

        distance = Geodesic.WGS84.Inverse(dlat, dlng, self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (pw.precision + pw.epsilon))
        self.polyline._last_pos = (dlat, dlng)
        self.assertTrue(abs(self.polyline.get_alt() - self.bot.position[2]) <= 1)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_bigger_then_total_speed(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min
        speed = 300
        precision = 0.0

        self.bot.config.walk_max = speed
        self.bot.config.walk_min = speed

        pw = PolylineWalker(self.bot, ex_dest[0], ex_dest[1], precision=precision)
        self.assertEqual(pw.dest_lat, ex_dest[0], 'dest_lat did not match')
        self.assertEqual(pw.dest_lng, ex_dest[1], 'dest_lng did not match')

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return pw.step()

        finishedWalking = run_step()
        self.assertTrue(finishedWalking, 'step should return False')

        distance = Geodesic.WGS84.Inverse(ex_dest[0], ex_dest[1], self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (pw.precision + pw.epsilon))
        self.polyline._last_pos = self.polyline.destination
        self.assertTrue(abs(self.polyline.get_alt() - self.bot.position[2]) <= 1)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_bigger_then_total_speed_big_precision_offset(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min
        speed = 300
        precision = 2.5

        self.bot.config.walk_max = speed
        self.bot.config.walk_min = speed

        pw = PolylineWalker(self.bot, ex_dest[0], ex_dest[1], precision=precision)
        self.assertEqual(pw.dest_lat, ex_dest[0], 'dest_lat did not match')
        self.assertEqual(pw.dest_lng, ex_dest[1], 'dest_lng did not match')

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return pw.step()

        finishedWalking = run_step()
        self.assertTrue(finishedWalking, 'step should return False')

        distance = Geodesic.WGS84.Inverse(ex_dest[0], ex_dest[1], self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (pw.precision + pw.epsilon))
        self.polyline._last_pos = self.polyline.destination
        self.assertTrue(abs(self.polyline.get_alt() - self.bot.position[2]) <= 1)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_stay_put(self):
        altitude = 429.5
        self.bot.position = [47.1706378, 8.5167405, altitude]
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min
        precision = 0.0
        speed = 0.0

        self.bot.config.walk_max = 4
        self.bot.config.walk_min = 2

        pw = PolylineWalker(self.bot, ex_dest[0], ex_dest[1], precision=precision)
        self.assertEqual(pw.dest_lat, ex_dest[0], 'dest_lat did not match')
        self.assertEqual(pw.dest_lng, ex_dest[1], 'dest_lng did not match')

        finishedWalking = pw.step(speed=speed)
        self.assertFalse(finishedWalking, 'step should return False')
        distance = Geodesic.WGS84.Inverse(ex_orig[0], ex_orig[1], self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (pw.precision + pw.epsilon))
        self.assertTrue(altitude - 1 <= self.bot.position[2] <= altitude + 1)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_teleport(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min
        precision = 0.0
        speed = float("inf")

        self.bot.config.walk_max = 4
        self.bot.config.walk_min = 2

        pw = PolylineWalker(self.bot, ex_dest[0], ex_dest[1], precision=precision)
        self.assertEqual(pw.dest_lat, ex_dest[0], 'dest_lat did not match')
        self.assertEqual(pw.dest_lng, ex_dest[1], 'dest_lng did not match')

        finishedWalking = pw.step(speed=speed)
        self.assertTrue(finishedWalking, 'step should return True')
        distance = Geodesic.WGS84.Inverse(ex_dest[0], ex_dest[1], self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (pw.precision + pw.epsilon))
        self.polyline._last_pos = self.polyline.destination
        self.assertTrue(abs(self.polyline.get_alt() - self.bot.position[2]) <= 1)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min
