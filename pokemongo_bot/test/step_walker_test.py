import unittest

from geographiclib.geodesic import Geodesic
from mock import MagicMock, patch, mock

from pokemongo_bot.walkers.step_walker import StepWalker

NORMALIZED_LAT_LNG_DISTANCE = (6.3948578954430175e-06, 6.35204828670955e-06)


class TestStepWalker(unittest.TestCase):
    def setUp(self):
        self.patcherSleep = patch('pokemongo_bot.walkers.step_walker.sleep')
        self.patcherSleep.start()

        self.bot = MagicMock()
        self.bot.position = [0, 0, 0]
        self.bot.api = MagicMock()

        # let us get back the position set by the StepWalker
        def api_set_position(lat, lng, alt):
            self.bot.position = [lat, lng, alt]
        self.bot.api.set_position = api_set_position

    def tearDown(self):
        self.bot.position = [0, 0, 0]
        self.patcherSleep.stop()

    def test_normalized_distance(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min

        self.bot.config.walk_max = 1
        self.bot.config.walk_min = 1

        sw = StepWalker(self.bot, 0.1, 0.1, precision=0.0)
        self.assertGreater(sw.dest_lat, 0)
        self.assertGreater(sw.dest_lng, 0)

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return sw.step()

        stayInPlace = run_step()
        self.assertFalse(stayInPlace)

        self.assertAlmostEqual(self.bot.position[0], NORMALIZED_LAT_LNG_DISTANCE[0], places=6)
        self.assertAlmostEqual(self.bot.position[1], NORMALIZED_LAT_LNG_DISTANCE[1], places=6)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_normalized_distance_times_2(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min

        self.bot.config.walk_max = 2
        self.bot.config.walk_min = 2

        sw = StepWalker(self.bot, 0.1, 0.1, precision=0.0)
        self.assertTrue(sw.dest_lat > 0)
        self.assertTrue(sw.dest_lng > 0)

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return sw.step()

        stayInPlace = run_step()
        self.assertFalse(stayInPlace)

        self.assertAlmostEqual(self.bot.position[0], NORMALIZED_LAT_LNG_DISTANCE[0] * 2, places=6)
        self.assertAlmostEqual(self.bot.position[1], NORMALIZED_LAT_LNG_DISTANCE[1] * 2, places=6)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_small_distance_same_spot(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min

        self.bot.config.walk_max = 1
        self.bot.config.walk_min = 1

        sw = StepWalker(self.bot, 0, 0, precision=0.0)
        self.assertEqual(sw.dest_lat, 0, 'dest_lat should be 0')
        self.assertEqual(sw.dest_lng, 0, 'dest_lng should be 0')

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return sw.step()
        moveInprecision = run_step()

        self.assertTrue(moveInprecision, 'step should return True')
        distance = Geodesic.WGS84.Inverse(0.0, 0.0, self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (sw.precision + sw.epsilon))

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_small_distance_small_step(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min

        self.bot.config.walk_max = 1
        self.bot.config.walk_min = 1

        # distance from origin 0,0 to 1e-6, 1e-6 is 0.157253373328 meters
        total_distance = Geodesic.WGS84.Inverse(0.0, 0.0, 1e-6, 1e-6)["s12"]
        # we take a precision bigger then the total value...
        sw = StepWalker(self.bot, 1e-6, 1e-6, precision=0.2)
        self.assertEqual(sw.dest_lat, 1e-6)
        self.assertEqual(sw.dest_lng, 1e-6)

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return sw.step()

        moveInprecistion = run_step()
        self.assertTrue(moveInprecistion, 'step should return True')

        distance = Geodesic.WGS84.Inverse(0.0, 0.0, self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= abs(total_distance - distance) <= (sw.precision + sw.epsilon))

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_big_distances(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min

        self.bot.config.walk_max = 1
        self.bot.config.walk_min = 1

        sw = StepWalker(self.bot, 10, 10, precision=0.0)
        self.assertEqual(sw.dest_lat, 10)
        self.assertEqual(sw.dest_lng, 10)

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return sw.step()

        finishedWalking = run_step()
        self.assertFalse(finishedWalking, 'step should return False')
        self.assertAlmostEqual(self.bot.position[0], NORMALIZED_LAT_LNG_DISTANCE[0], places=6)

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_stay_put(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min

        self.bot.config.walk_max = 4
        self.bot.config.walk_min = 2

        sw = StepWalker(self.bot, 10, 10, precision=0.0)
        self.assertEqual(sw.dest_lat, 10)
        self.assertEqual(sw.dest_lng, 10)

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return sw.step(speed=0)

        finishedWalking = run_step()
        self.assertFalse(finishedWalking, 'step should return False')
        distance = Geodesic.WGS84.Inverse(0.0, 0.0, self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= distance <= (sw.precision + sw.epsilon))

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min

    def test_teleport(self):
        walk_max = self.bot.config.walk_max
        walk_min = self.bot.config.walk_min

        self.bot.config.walk_max = 4
        self.bot.config.walk_min = 2

        sw = StepWalker(self.bot, 10, 10, precision=0.0)
        self.assertEqual(sw.dest_lat, 10)
        self.assertEqual(sw.dest_lng, 10)

        @mock.patch('random.uniform')
        def run_step(mock_random):
            mock_random.return_value = 0.0
            return sw.step(speed=float("inf"))

        finishedWalking = run_step()
        self.assertTrue(finishedWalking, 'step should return True')
        total_distance = Geodesic.WGS84.Inverse(0.0, 0.0, 10, 10)["s12"]
        distance = Geodesic.WGS84.Inverse(0.0, 0.0, self.bot.position[0], self.bot.position[1])["s12"]
        self.assertTrue(0.0 <= abs(total_distance - distance) <= (sw.precision + sw.epsilon))

        self.bot.config.walk_max = walk_max
        self.bot.config.walk_min = walk_min
