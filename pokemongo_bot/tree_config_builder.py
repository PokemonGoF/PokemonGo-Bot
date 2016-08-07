import cell_workers
from pokemongo_bot.plugin_loader import PluginLoader

class ConfigException(Exception):
    pass

class TreeConfigBuilder(object):
    def __init__(self, bot, tasks_raw):
        self.bot = bot
        self.tasks_raw = tasks_raw
        self.plugin_loader = PluginLoader()

    def _get_worker_by_name(self, name):
        try:
            worker = getattr(cell_workers, name)
        except AttributeError:
            raise ConfigException('No worker named {} defined'.format(name))

        return worker

    def _is_plugin_task(self, name):
        return '.' in name

    def build(self):
        workers = []

        for task in self.tasks_raw:
            task_type = task.get('type', None)
            if task_type is None:
                raise ConfigException('No type found for given task {}'.format(task))
            elif task_type == 'EvolveAll':
                raise ConfigException('The EvolveAll task has been renamed to EvolvePokemon')

            task_config = task.get('config', {})

            if self._is_plugin_task(task_type):
                worker = self.plugin_loader.get_class(task_type)
            else:
                worker = self._get_worker_by_name(task_type)

            instance = worker(self.bot, task_config)
            workers.append(instance)

        return workers

