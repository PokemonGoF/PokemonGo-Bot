import os
import pickle
import unittest
import requests_mock
from pokemongo_bot.walkers.polyline_generator import Polyline

ex_orig = (47.1706378, 8.5167405)
ex_dest = (47.1700271, 8.518072999999998)
ex_speed = 2.5
ex_total_distance = 194
ex_resp_directions = 'example_directions.pickle'
ex_resp_elevations = 'example_elevations.pickle'
ex_enc_polyline = 'o_%7C~Gsl~r@??h@LVDf@LDcBFi@AUEUQg@EKCI?G?GBG@EBEJKNC??'
ex_nr_samples = 64


class PolylineTestCase(unittest.TestCase):
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
            self.polyline = Polyline(ex_orig, ex_dest)

    def test_first_point(self):
        self.assertEqual(self.polyline._points[0], ex_orig)

    def test_last_point(self):
        self.assertEqual(self.polyline._points[-1], ex_dest)

    def test_nr_of_elevations_returned(self):
        total_seconds = self.polyline.get_total_distance() / 3
        self.assertAlmostEqual(total_seconds, ex_nr_samples, places=0)

    def test_total_distance(self):
        self.assertEquals(self.polyline.get_total_distance(), ex_total_distance)

    def test_get_last_pos(self):
        self.assertEquals(self.polyline.get_last_pos(), self.polyline._last_pos)
