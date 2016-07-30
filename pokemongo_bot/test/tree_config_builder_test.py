import unittest
import json
from pokemongo_bot import PokemonGoBot, ConfigException, TreeConfigBuilder
from pokemongo_bot.cell_workers import SoftBan, CatchLuredPokemon

def convert_from_json(str):
    return json.loads(str)

class TreeConfigBuilderTest(unittest.TestCase):
    def setUp(self):
        self.bot = {}

    def test_should_throw_on_no_type_key(self):
        obj = convert_from_json("""[{
                "bad_key": "foo"
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)

        self.assertRaisesRegexp(
            ConfigException,
            "No type found for given task",
            builder.build)

    def test_should_throw_on_non_matching_type(self):
        obj = convert_from_json("""[{
                "type": "foo"
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)

        self.assertRaisesRegexp(
            ConfigException,
            "No worker named foo defined",
            builder.build)

    def test_creating_worker(self):
        obj = convert_from_json("""[{
                "type": "SoftBan"
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)
        tree = builder.build()

        self.assertIsInstance(tree[0], SoftBan)
        self.assertIs(tree[0].bot, self.bot)

    def test_creating_two_workers(self):
        obj = convert_from_json("""[{
                "type": "SoftBan"
            }, {
                "type": "CatchLuredPokemon"
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)
        tree = builder.build()

        self.assertIsInstance(tree[0], SoftBan)
        self.assertIs(tree[0].bot, self.bot)
        self.assertIsInstance(tree[1], CatchLuredPokemon)
        self.assertIs(tree[1].bot, self.bot)

if __name__ == '__main__':
    unittest.main()
