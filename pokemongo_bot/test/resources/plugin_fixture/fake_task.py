from pokemongo_bot.base_task import BaseTask

class FakeTask(BaseTask):
  SUPPORTED_TASK_API_VERSION = 1

  def work(self):
    return 'FakeTask'
