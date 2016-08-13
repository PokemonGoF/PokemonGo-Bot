import os
import sys
import importlib
import re
import requests
import zipfile
import shutil

class PluginLoader(object):
  folder_cache = []

  def _get_correct_path(self, path):
    extension = os.path.splitext(path)[1]

    if extension == '.zip':
      correct_path = path
    else:
      correct_path = os.path.dirname(path)

    return correct_path

  def load_plugin(self, plugin):
    github_plugin = GithubPlugin(plugin)
    if github_plugin.is_valid_plugin():
      if not github_plugin.is_already_installed():
        github_plugin.install()

      correct_path = github_plugin.get_plugin_folder()

    else:
      correct_path = self._get_correct_path(plugin)

    if correct_path not in self.folder_cache:
      self.folder_cache.append(correct_path)
      sys.path.append(correct_path)

  def remove_path(self, path):
    correct_path = self._get_correct_path(path)
    sys.path.remove(correct_path)
    self.folder_cache.remove(correct_path)

  def get_class(self, namespace_class):
    [namespace, class_name] = namespace_class.split('.')
    my_module = importlib.import_module(namespace)
    return getattr(my_module, class_name)

class GithubPlugin(object):
  PLUGINS_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'plugins')

  def __init__(self, plugin_name):
    self.plugin_name = plugin_name
    self.plugin_parts = self.get_github_parts()

  def is_valid_plugin(self):
    return self.plugin_parts is not None

  def get_github_parts(self):
    groups = re.match('(.*)\/(.*)#(.*)', self.plugin_name)

    if groups is None:
      return None

    parts = {}
    parts['user'] = groups.group(1)
    parts['repo'] = groups.group(2)
    parts['sha'] = groups.group(3)

    return parts

  def get_installed_version(self):
    if not self.is_already_installed():
      return None

    filename = os.path.join(self.get_plugin_folder(), '.sha')
    print filename
    with open(filename) as file:
        return file.read().strip()

  def get_local_destination(self):
    parts = self.plugin_parts
    if parts is None:
      raise Exception('Not a valid github plugin')

    file_name = '{}_{}_{}.zip'.format(parts['user'], parts['repo'], parts['sha'])
    full_path = os.path.join(self.PLUGINS_FOLDER, file_name)
    return full_path

  def is_already_installed(self):
    file_path = self.get_plugin_folder()
    if not os.path.isdir(file_path):
      return False

    sha_file = os.path.join(file_path, '.sha')

    if not os.path.isfile(sha_file):
      return False

    with open(sha_file) as file:
      content = file.read().strip()

      if content != self.plugin_parts['sha']:
        return False

    return True

  def get_plugin_folder(self):
    folder_name = '{}_{}'.format(self.plugin_parts['user'], self.plugin_parts['repo'])
    return os.path.join(self.PLUGINS_FOLDER, folder_name)

  def get_github_download_url(self):
    parts = self.plugin_parts
    if parts is None:
      raise Exception('Not a valid github plugin')

    github_url = 'https://github.com/{}/{}/archive/{}.zip'.format(parts['user'], parts['repo'], parts['sha'])
    return github_url

  def install(self):
    self.download()
    self.extract()

  def extract(self):
    dest = self.get_plugin_folder()
    with zipfile.ZipFile(self.get_local_destination(), "r") as z:
      z.extractall(dest)

    github_folder = os.path.join(dest, '{}-{}'.format(self.plugin_parts['repo'], self.plugin_parts['sha']))
    new_folder = os.path.join(dest, '{}'.format(self.plugin_parts['repo']))
    shutil.move(github_folder, new_folder)

    with open(os.path.join(dest, '.sha'), 'w') as file:
      file.write(self.plugin_parts['sha'])

    os.remove(self.get_local_destination())

  def download(self):
    url = self.get_github_download_url()
    dest = self.get_local_destination()

    r = requests.get(url, stream=True)
    r.raise_for_status()

    with open(dest, 'wb') as f:
      for chunk in r.iter_content(chunk_size=1024):
        if chunk:
          f.write(chunk)
    r.close()
    return dest
