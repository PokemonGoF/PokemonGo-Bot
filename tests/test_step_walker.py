from mock import Mock, MagicMock, patch
from nose.tools import ok_, eq_, raises, timed, TimeExpired

from pokemongo_bot.step_walker import StepWalker
from pokemongo_bot.constants import Constants
from pokemongo_bot.cell_workers.utils import float_equal

NORMALIZED_LAT_LNG_DISTANCE_STEP = 6.3593e-6

class TestStepWalker(object):
    def setup(self):
        self.patcherSleep = patch('pokemongo_bot.step_walker.sleep')
        self.patcherRandomLat = patch('pokemongo_bot.step_walker.random_lat_long_delta', return_value=0)
        self.patcherSleep.start()
        self.patcherRandomLat.start()

        self.bot = MagicMock()
        self.bot.position = [0, 0, 0]
        self.bot.api = MagicMock()

        self.lat, self.lng, self.alt = 0, 0, 0
        def api_set_position(lat, lng, alt):
            self.lat, self.lng, self.alt = lat, lng, alt
        self.bot.api.set_position = api_set_position

    def teardown(self):
        self.patcherSleep.stop()
        self.patcherRandomLat.stop()

    def test_normalized_distance(self):
        sw = StepWalker(self.bot, 1, 0.1, 0.1)
        ok_(sw.dLat > 0)
        ok_(sw.dLng > 0)

        flag = sw.step()
        ok_(flag != True)

        ok_(float_equal(self.lat, NORMALIZED_LAT_LNG_DISTANCE_STEP))
        ok_(float_equal(self.lng, NORMALIZED_LAT_LNG_DISTANCE_STEP))

    def test_normalized_distance_times_2(self):
        sw = StepWalker(self.bot, 2, 0.1, 0.1)
        ok_(sw.dLat > 0)
        ok_(sw.dLng > 0)

        flag = sw.step()
        ok_(flag != True)

        ok_(float_equal(self.lat, NORMALIZED_LAT_LNG_DISTANCE_STEP * 2))
        ok_(float_equal(self.lng, NORMALIZED_LAT_LNG_DISTANCE_STEP * 2))

    def test_small_distance_same_spot(self):
        sw = StepWalker(self.bot, 1, 0, 0)
        ok_(sw.dLat == 0)
        ok_(sw.dLng == 0)

        ok_(sw.step() == True)
        ok_(self.lat == self.bot.position[0])
        ok_(self.lng == self.bot.position[1])

    def test_small_distance_small_step(self):
        sw = StepWalker(self.bot, 1, 1e-5, 1e-5)
        ok_(sw.dLat == 0)
        ok_(sw.dLng == 0)

    @raises(RuntimeError)
    def test_big_distances(self):
        sw = StepWalker(self.bot, 1, 10, 10)
