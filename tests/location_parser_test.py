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
            favorite_locations=[
                {"name": "Paris", "coords": "23.3333,23.3333"},
                {"name": "Sofia", "coords": "30.000,30.000"}
            ],
            location_cache=False,
            username='Foobar',
        )
        self.bot.alt = 8
        self.bot.logger = MagicMock(return_value="")
        self.bot.updateConfig(config)

    def test_named_position(self):
        position = (42, 42, 0)
        self.bot.get_pos_by_name = MagicMock(return_value=position)
        self.bot._set_starting_position()
        self.assertEqual(self.bot.position, position)

    def test_find_fav_location(self):
        expected_position = (23.3333, 23.3333, 8)
        actual_position = self.bot.get_pos_by_name(self.bot.config.location)
        self.assertEqual(actual_position, expected_position)

    def test_get_pos_by_fav_location(self):
        expected_position = (23.3333,23.3333,8)
        actual_position = self.bot._get_pos_by_fav_location(self.bot.config.location)
        self.assertEqual(expected_position, actual_position)

    def test_no_favorite_position(self):
        result = self.bot._get_pos_by_fav_location("NOT_EXIST")
        self.assertEqual(result,None)

    def test_empty_favorite_position(self):
        config = dict(
            favorite_locations=[],
        )
        self.bot.updateConfig(config)

        result = self.bot._get_pos_by_fav_location("Does not matter")
        self.assertEqual(result,None)

    def test_named_position_utf8(self):
        position = (42, 42, 0)
        self.bot.config.location = u"àéùƱǣЊ؍ ข᠃"
        self.bot.get_pos_by_name = MagicMock(return_value=position)

        self.bot._set_starting_position()
        self.assertEqual(self.bot.position, position)
