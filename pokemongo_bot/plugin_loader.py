import os
import sys
import importlib
import re
import requests

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
    correct_path = self._get_correct_path(plugin)

    if correct_path not in self.folder_cache:
      self.folder_cache.append(correct_path)
      sys.path.append(correct_path)

  def remove_path(self, path):
    correct_path = self._get_correct_path(path)
    sys.path.remove(correct_path)

  def get_class(self, namespace_class):
    [namespace, class_name] = namespace_class.split('.')
    my_module = importlib.import_module(namespace)
    return getattr(my_module, class_name)

class GithubPlugin(object):
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

  def get_local_destination(self):
    parts = self.plugin_parts
    if parts is None:
      raise Exception('Not a valid github plugin')

    file_name = '{}_{}_{}.zip'.format(parts['user'], parts['repo'], parts['sha'])
    full_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'plugins', file_name)
    return full_path

  def get_github_download_url(self):
    parts = self.plugin_parts
    if parts is None:
      raise Exception('Not a valid github plugin')

    github_url = 'https://github.com/{}/{}/archive/{}.zip'.format(parts['user'], parts['repo'], parts['sha'])
    return github_url

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
