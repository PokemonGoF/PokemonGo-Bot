from pokemongo_bot.base_task import BaseTask

class FakeTask(BaseTask):
  def work(self):
    return 'FakeTask'
