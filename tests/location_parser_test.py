# coding: utf-8
import unittest
from mock import MagicMock

from geopy.exc import GeocoderQueryError
from tests import FakeBot


class TestLocationParser(unittest.TestCase):

    def setUp(self):
        self.bot = FakeBot()
        config = dict(
            test=False,
            location='Paris',
            location_cache=False,
            username='Foobar',
        )
        self.bot.updateConfig(config)

    def test_named_position(self):
        position = (42, 42, 0)
        self.bot.get_pos_by_name = MagicMock(return_value=position)
        self.bot._set_starting_position()
        self.assertEqual(self.bot.position, position)

    def test_named_position_utf8(self):
        position = (42, 42, 0)
        self.bot.config.location = u"àéùƱǣЊ؍ ข᠃"
        self.bot.get_pos_by_name = MagicMock(return_value=position)

        self.bot._set_starting_position()
        self.assertEqual(self.bot.position, position)
