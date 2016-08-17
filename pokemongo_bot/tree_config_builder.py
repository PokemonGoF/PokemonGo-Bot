import cell_workers
from pokemongo_bot.plugin_loader import PluginLoader
from pokemongo_bot.base_task import BaseTask

class ConfigException(Exception):
    pass

class MismatchTaskApiVersion(Exception):
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
        deprecated_pokemon_task = False

        for task in self.tasks_raw:
            task_type = task.get('type', None)
            if task_type is None:
                raise ConfigException('No type found for given task {}'.format(task))
            elif task_type == 'EvolveAll':
                raise ConfigException('The EvolveAll task has been renamed to EvolvePokemon')

            task_config = task.get('config', {})

            if task_type in ['CatchVisiblePokemon', 'CatchLuredPokemon']:
                if deprecated_pokemon_task:
                    continue
                else:
                    deprecated_pokemon_task = True
                    task_type = 'CatchPokemon'
                    task_config = {}
                    self.bot.logger.warning('The CatchVisiblePokemon & CatchLuredPokemon tasks have been replaced with '
                                            'CatchPokemon.  CatchPokemon has been enabled with default settings.')

            if self._is_plugin_task(task_type):
                worker = self.plugin_loader.get_class(task_type)
            else:
                worker = self._get_worker_by_name(task_type)

            error_string = ''
            if BaseTask.TASK_API_VERSION < worker.SUPPORTED_TASK_API_VERSION:
                error_string = 'Do you need to update the bot?'

            elif BaseTask.TASK_API_VERSION > worker.SUPPORTED_TASK_API_VERSION:
                error_string = 'Is there a new version of this task?'

            if error_string != '':
                raise MismatchTaskApiVersion(
                    'Task {} only works with task api version {}, you are currently running version {}. {}'
                    .format(
                        task_type,
                        worker.SUPPORTED_TASK_API_VERSION,
                        BaseTask.TASK_API_VERSION,
                        error_string
                    )
                )

            instance = worker(self.bot, task_config)
            if instance.enabled:
                workers.append(instance)

        return workers
