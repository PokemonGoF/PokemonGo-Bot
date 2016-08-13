import unittest
from mock import MagicMock, patch

from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.cell_workers.utils import float_equal

NORMALIZED_LAT_LNG_DISTANCE_STEP = 6.3593e-6

class TestStepWalker(unittest.TestCase):
    def setUp(self):
        self.patcherSleep = patch('pokemongo_bot.step_walker.sleep')
        self.patcherRandomLat = patch('pokemongo_bot.step_walker.random_lat_long_delta', return_value=0)
        self.patcherSleep.start()
        self.patcherRandomLat.start()

        self.bot = MagicMock()
        self.bot.position = [0, 0, 0]
        self.bot.api = MagicMock()

        self.lat, self.lng, self.alt = 0, 0, 0

        # let us get back the position set by the StepWalker
        def api_set_position(lat, lng, alt):
            self.lat, self.lng, self.alt = lat, lng, alt
        self.bot.api.set_position = api_set_position

    def tearDown(self):
        self.patcherSleep.stop()
        self.patcherRandomLat.stop()

    def test_normalized_distance(self):
        sw = StepWalker(self.bot, 1, 0.1, 0.1)
        self.assertGreater(sw.dLat, 0)
        self.assertGreater(sw.dLng, 0)

        stayInPlace = sw.step()
        self.assertFalse(stayInPlace)

        self.assertTrue(float_equal(self.lat, NORMALIZED_LAT_LNG_DISTANCE_STEP))
        self.assertTrue(float_equal(self.lng, NORMALIZED_LAT_LNG_DISTANCE_STEP))

    def test_normalized_distance_times_2(self):
        sw = StepWalker(self.bot, 2, 0.1, 0.1)
        self.assertTrue(sw.dLat > 0)
        self.assertTrue(sw.dLng > 0)

        stayInPlace = sw.step()
        self.assertFalse(stayInPlace)

        self.assertTrue(float_equal(self.lat, NORMALIZED_LAT_LNG_DISTANCE_STEP * 2))
        self.assertTrue(float_equal(self.lng, NORMALIZED_LAT_LNG_DISTANCE_STEP * 2))

    def test_small_distance_same_spot(self):
        sw = StepWalker(self.bot, 1, 0, 0)
        self.assertEqual(sw.dLat, 0, 'dLat should be 0')
        self.assertEqual(sw.dLng, 0, 'dLng should be 0')

        self.assertTrue(sw.step(), 'step should return True')
        self.assertTrue(self.lat == self.bot.position[0])
        self.assertTrue(self.lng == self.bot.position[1])

    def test_small_distance_small_step(self):
        sw = StepWalker(self.bot, 1, 1e-5, 1e-5)
        self.assertEqual(sw.dLat, 0)
        self.assertEqual(sw.dLng, 0)

    @unittest.skip('This behavior is To Be Defined')
    def test_big_distances(self):
        # FIXME currently the StepWalker acts like it won't move if big distances gives as input
        # see args below
        # with self.assertRaises(RuntimeError):
        sw = StepWalker(self.bot, 1, 10, 10)
        sw.step() # equals True i.e act like the distance is too short for a step
