import os
import sys
import importlib

class PluginLoader(object):
  folder_cache = []

  def load_path(self, path):
    if path not in self.folder_cache:
      self.folder_cache.append(path)
      sys.path.append(path)

  def remove_path(self, path):
    sys.path.remove(path)

  def get_class(self, namespace_class):
    [namespace, class_name] = namespace_class.split('.')
    my_module = importlib.import_module(namespace)
    return getattr(my_module, class_name)

