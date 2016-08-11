import unittest
import json
import os
from pokemongo_bot import PokemonGoBot, ConfigException, MismatchTaskApiVersion, TreeConfigBuilder, PluginLoader, BaseTask
from pokemongo_bot.cell_workers import HandleSoftBan, CatchLuredPokemon
from pokemongo_bot.test.resources.plugin_fixture import FakeTask, UnsupportedApiTask

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

    def test_should_throw_on_wrong_evolve_task_name(self):
        obj = convert_from_json("""[{
                "type": "EvolveAll"
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)

        self.assertRaisesRegexp(
            ConfigException,
            "The EvolveAll task has been renamed to EvolvePokemon",
            builder.build)

    def test_creating_worker(self):
        obj = convert_from_json("""[{
                "type": "HandleSoftBan"
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)
        tree = builder.build()

        self.assertIsInstance(tree[0], HandleSoftBan)
        self.assertIs(tree[0].bot, self.bot)

    def test_creating_two_workers(self):
        obj = convert_from_json("""[{
                "type": "HandleSoftBan"
            }, {
                "type": "CatchLuredPokemon"
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)
        tree = builder.build()

        self.assertIsInstance(tree[0], HandleSoftBan)
        self.assertIs(tree[0].bot, self.bot)
        self.assertIsInstance(tree[1], CatchLuredPokemon)
        self.assertIs(tree[1].bot, self.bot)

    def test_task_with_config(self):
        obj = convert_from_json("""[{
                "type": "IncubateEggs",
                "config": {
                    "longer_eggs_first": true
                }
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)
        tree = builder.build()
        self.assertTrue(tree[0].config.get('longer_eggs_first', False))

    def test_disabling_task(self):
        obj = convert_from_json("""[{
                "type": "HandleSoftBan",
                "config": {
                    "enabled": false
                }
            }, {
                "type": "CatchLuredPokemon",
                "config": {
                    "enabled": true
                }
            }]""")

        builder = TreeConfigBuilder(self.bot, obj)
        tree = builder.build()

        self.assertTrue(len(tree) == 1)
        self.assertIsInstance(tree[0], CatchLuredPokemon)

    def test_load_plugin_task(self):
        package_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'plugin_fixture')
        plugin_loader = PluginLoader()
        plugin_loader.load_plugin(package_path)

        obj = convert_from_json("""[{
            "type": "plugin_fixture.FakeTask"
        }]""")

        builder = TreeConfigBuilder(self.bot, obj)
        tree = builder.build()
        result = tree[0].work()
        self.assertEqual(result, 'FakeTask')

    def setupUnsupportedBuilder(self):
        package_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'pokemongo_bot', 'test', 'resources', 'plugin_fixture')
        plugin_loader = PluginLoader()
        plugin_loader.load_plugin(package_path)

        obj = convert_from_json("""[{
            "type": "plugin_fixture.UnsupportedApiTask"
        }]""")

        return TreeConfigBuilder(self.bot, obj)

    def test_task_version_too_high(self):
        builder = self.setupUnsupportedBuilder()

        previous_version = BaseTask.TASK_API_VERSION
        BaseTask.TASK_API_VERSION = 1

        self.assertRaisesRegexp(
            MismatchTaskApiVersion,
            "Task plugin_fixture.UnsupportedApiTask only works with task api version 2, you are currently running version 1. Do you need to update the bot?",
            builder.build)

        BaseTask.TASK_API_VERSION = previous_version

    def test_task_version_too_low(self):
        builder = self.setupUnsupportedBuilder()

        previous_version = BaseTask.TASK_API_VERSION
        BaseTask.TASK_API_VERSION = 3

        self.assertRaisesRegexp(
            MismatchTaskApiVersion,
            "Task plugin_fixture.UnsupportedApiTask only works with task api version 2, you are currently running version 3. Is there a new version of this task?",
            builder.build)

        BaseTask.TASK_API_VERSION = previous_version
