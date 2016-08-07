import os
import sys
import importlib

class PluginLoader(object):
  folder_cache = []

  def load_path(self, path):
    parent_dir = os.path.dirname(path)
    if parent_dir not in self.folder_cache:
      self.folder_cache.append(parent_dir)
      sys.path.append(parent_dir)

  def get_class(self, namespace_class):
    [namespace, class_name] = namespace_class.split('.')
    my_module = importlib.import_module(namespace)
    return getattr(my_module, class_name)

