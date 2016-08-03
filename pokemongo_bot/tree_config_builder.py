import cell_workers

class ConfigException(Exception):
    pass

class TreeConfigBuilder(object):
    def __init__(self, bot, tasks_raw):
        self.bot = bot
        self.tasks_raw = tasks_raw

    def _get_worker_by_name(self, name):
        try:
            worker = getattr(cell_workers, name)
        except AttributeError:
            raise ConfigException('No worker named {} defined'.format(name))

        return worker

    def build(self):
        workers = []

        for task in self.tasks_raw:
            task_type = task.get('type', None)
            if task_type is None:
                raise ConfigException('No type found for given task {}'.format(task))
            elif task_type == 'EvolveAll':
                raise ConfigException('The EvolveAll task has been renamed to EvolvePokemon')

            task_config = task.get('config', {})

            worker = self._get_worker_by_name(task_type)
            instance = worker(self.bot, task_config)
            workers.append(instance)

        return workers

