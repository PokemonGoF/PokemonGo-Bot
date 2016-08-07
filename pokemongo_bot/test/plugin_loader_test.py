import imp
import sys
import pkgutil
import importlib
import unittest
import os
from datetime import timedelta, datetime
from mock import patch, MagicMock
from pokemongo_bot.plugin_loader import PluginLoader
from pokemongo_bot.test.resources.plugin_fixture import FakeTask

class PluginLoaderTest(unittest.TestCase):
    def setUp(self):
        self.plugin_loader = PluginLoader()

    def test_load_namespace_class(self):
        package_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'plugin_fixture')
        self.plugin_loader.load_plugin(package_path)
        loaded_class = self.plugin_loader.get_class('plugin_fixture.FakeTask')
        self.assertEqual(loaded_class({}, {}).work(), 'FakeTask')
        self.plugin_loader.remove_path(package_path)

    def test_load_zip(self):
        package_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'plugin_fixture_test.zip')
        self.plugin_loader.load_plugin(package_path)
        loaded_class = self.plugin_loader.get_class('plugin_fixture_test.FakeTask')
        self.assertEqual(loaded_class({}, {}).work(), 'FakeTask')
        self.plugin_loader.remove_path(package_path)
