import os
import sys
import importlib

class PluginLoader(object):
  folder_cache = []

  def _get_correct_path(self, path):
    extension = os.path.splitext(path)[1]

    if extension == '.zip':
      correct_path = path
    else:
      correct_path = os.path.dirname(path)

    return correct_path

  def load_plugin(self, path):
    correct_path = self._get_correct_path(path)

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

