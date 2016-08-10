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

PLUGIN_PATH = os.path.realpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'plugins'))

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

    def copy_plugin(self):
        package_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'plugin_fixture')
        dest_path = os.path.join(PLUGIN_PATH, 'org_repo', 'plugin_fixture_tests')
        shutil.copytree(package_path, os.path.join(dest_path))
        with open(os.path.join(os.path.dirname(dest_path), '.sha'), 'w') as file:
            file.write('testsha')
        return dest_path

    def test_load_github_already_downloaded(self):
        dest_path = self.copy_plugin()
        self.plugin_loader.load_plugin('org/repo#testsha')
        loaded_class = self.plugin_loader.get_class('plugin_fixture_tests.FakeTask')
        self.assertEqual(loaded_class({}, {}).work(), 'FakeTask')
        self.plugin_loader.remove_path(dest_path)
        shutil.rmtree(os.path.dirname(dest_path))

    def copy_zip(self):
        zip_name = 'test-pgo-plugin-2d54eddde33061be9b329efae0cfb9bd58842655.zip'
        fixture_zip = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', zip_name)
        zip_dest = os.path.join(PLUGIN_PATH, 'org_test-pgo-plugin_2d54eddde33061be9b329efae0cfb9bd58842655.zip')
        shutil.copyfile(fixture_zip, zip_dest)

    @mock.patch.object(GithubPlugin, 'download', copy_zip)
    def test_load_github_not_downloaded(self):
        self.plugin_loader.load_plugin('org/test-pgo-plugin#2d54eddde33061be9b329efae0cfb9bd58842655')
        loaded_class = self.plugin_loader.get_class('test-pgo-plugin.PrintText')
        self.assertEqual(loaded_class({}, {}).work(), 'PrintText')
        dest_path = os.path.join(PLUGIN_PATH, 'org_test-pgo-plugin')
        self.plugin_loader.remove_path(os.path.join(dest_path, 'test-pgo-plugin'))
        shutil.rmtree(dest_path)

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

    def test_get_installed_version(self):
        github_plugin = GithubPlugin('org/repo#my-version')
        src_fixture = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'plugin_sha')
        dest = github_plugin.get_plugin_folder()
        shutil.copytree(src_fixture, dest)
        actual = github_plugin.get_installed_version()
        shutil.rmtree(dest)
        self.assertEqual('my-version', actual)

    def test_get_plugin_folder(self):
        github_plugin = GithubPlugin('org/repo#sha')
        expected = os.path.join(PLUGIN_PATH, 'org_repo')
        actual = github_plugin.get_plugin_folder()
        self.assertEqual(actual, expected)

    def test_get_local_destination(self):
        github_plugin = GithubPlugin('org/repo#sha')
        path = github_plugin.get_local_destination()
        expected = os.path.join(PLUGIN_PATH, 'org_repo_sha.zip')
        self.assertEqual(path, expected)

    def test_get_github_download_url(self):
        github_plugin = GithubPlugin('org/repo#sha')
        url = github_plugin.get_github_download_url()
        expected = 'https://github.com/org/repo/archive/sha.zip'
        self.assertEqual(url, expected)

    def test_is_already_installed_not_installed(self):
        github_plugin = GithubPlugin('org/repo#sha')
        self.assertFalse(github_plugin.is_already_installed())

    def test_is_already_installed_version_mismatch(self):
        github_plugin = GithubPlugin('org/repo#sha')
        plugin_folder = github_plugin.get_plugin_folder()
        os.mkdir(plugin_folder)
        with open(os.path.join(plugin_folder, '.sha'), 'w') as file:
            file.write('sha2')

        actual = github_plugin.is_already_installed()
        shutil.rmtree(plugin_folder)
        self.assertFalse(actual)

    def test_is_already_installed_installed(self):
        github_plugin = GithubPlugin('org/repo#sha')
        plugin_folder = github_plugin.get_plugin_folder()
        os.mkdir(plugin_folder)
        with open(os.path.join(plugin_folder, '.sha'), 'w') as file:
            file.write('sha')

        actual = github_plugin.is_already_installed()
        shutil.rmtree(plugin_folder)
        self.assertTrue(actual)

    def test_extract(self):
        github_plugin = GithubPlugin('org/test-pgo-plugin#2d54eddde33061be9b329efae0cfb9bd58842655')
        src = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources', 'test-pgo-plugin-2d54eddde33061be9b329efae0cfb9bd58842655.zip')
        zip_dest = github_plugin.get_local_destination()
        shutil.copyfile(src, zip_dest)
        github_plugin.extract()
        plugin_folder = github_plugin.get_plugin_folder()
        os.path.isdir(plugin_folder)
        sub_folder = os.path.join(plugin_folder, 'test-pgo-plugin')
        os.path.isdir(sub_folder)
        sha_file = os.path.join(github_plugin.get_plugin_folder(), '.sha')
        os.path.isfile(sha_file)

        with open(sha_file) as file:
            content = file.read().strip()
            self.assertEqual(content, '2d54eddde33061be9b329efae0cfb9bd58842655')

        shutil.rmtree(plugin_folder)
