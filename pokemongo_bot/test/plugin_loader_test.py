import imp
import sys
import pkgutil
import importlib
import unittest
import os
import shutil
import mock
from datetime import timedelta, datetime
from mock import patch, MagicMock
from pokemongo_bot.plugin_loader import PluginLoader, GithubPlugin
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
        self.assertEqual(loaded_class({}, {}).work(), 'FakeTaskZip')
        self.plugin_loader.remove_path(package_path)

    def copy_zip(self):
        zip_fixture = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'plugin_fixture_test.zip')
        dest_path = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'plugins', 'org_repo_sha.zip'))
        shutil.copyfile(zip_fixture, dest_path)
        return dest_path

    def test_load_github_already_downloaded(self):
        dest_path = self.copy_zip()
        self.plugin_loader.load_plugin('org/repo#sha')
        loaded_class = self.plugin_loader.get_class('plugin_fixture_test.FakeTask')
        self.assertEqual(loaded_class({}, {}).work(), 'FakeTaskZip')
        self.plugin_loader.remove_path(dest_path)
        os.remove(dest_path)

    # def test_load_github_zip(self):
    #     package_path = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'plugins', 'TheSavior_test-pgo-plugin_master.zip'))
    #     self.plugin_loader.load_plugin(package_path)
    #     print
    #     print
    #     print sys.path
    #     # loaded_class({}, {}).work()
    #     print
    #     print
    #     # self.assertEqual(loaded_class({}, {}).work(), 'FakeTaskZip')
    #     loaded_class = self.plugin_loader.get_class('test-pgo-plugin-2d54eddde33061be9b329efae0cfb9bd58842655.PrintText')
    #     self.assertEqual(loaded_class({}, {}).work(), 'FakeTaskZip')
    #     self.plugin_loader.remove_path(package_path)

    @mock.patch.object(GithubPlugin, 'download', copy_zip)
    def test_load_github_not_downloaded(self):
        self.plugin_loader.load_plugin('org/repo#sha')
        loaded_class = self.plugin_loader.get_class('plugin_fixture_test.FakeTask')
        self.assertEqual(loaded_class({}, {}).work(), 'FakeTaskZip')
        dest_path = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'plugins', 'org_repo_sha.zip'))
        self.plugin_loader.remove_path(dest_path)
        os.remove(dest_path)

class GithubPluginTest(unittest.TestCase):
    def test_get_github_parts_for_valid_github(self):
        github_plugin = GithubPlugin('org/repo#sha')
        self.assertTrue(github_plugin.is_valid_plugin())
        self.assertEqual(github_plugin.plugin_parts['user'], 'org')
        self.assertEqual(github_plugin.plugin_parts['repo'], 'repo')
        self.assertEqual(github_plugin.plugin_parts['sha'], 'sha')

    def test_get_github_parts_for_invalid_github(self):
        self.assertFalse(GithubPlugin('org/repo').is_valid_plugin())
        self.assertFalse(GithubPlugin('foo').is_valid_plugin())
        self.assertFalse(GithubPlugin('/Users/foo/bar.zip').is_valid_plugin())

    def test_get_plugin_folder(self):
        github_plugin = GithubPlugin('org/repo#sha')
        expected = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'plugins', 'org_repo'))
        actual = github_plugin.get_plugin_folder()
        self.assertEqual(actual, expected)

    def test_get_local_destination(self):
        github_plugin = GithubPlugin('org/repo#sha')
        path = github_plugin.get_local_destination()
        expected = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'plugins', 'org_repo_sha.zip'))
        self.assertEqual(path, expected)

    def test_get_github_download_url(self):
        github_plugin = GithubPlugin('org/repo#sha')
        url = github_plugin.get_github_download_url()
        expected = 'https://github.com/org/repo/archive/sha.zip'
        self.assertEqual(url, expected)

    def test_is_already_installed_not_downloaded(self):
        github_plugin = GithubPlugin('org/repo#sha')
        self.assertFalse(github_plugin.is_already_installed())

    def test_is_already_installed_downloaded(self):
        github_plugin = GithubPlugin('org/repo#sha')
        dest = github_plugin.get_local_destination()
        open(dest, 'a').close()
        self.assertTrue(github_plugin.is_already_installed())
        os.remove(dest)
