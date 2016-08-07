from pokemongo_bot.cell_workers import BaseTask

class FakeTask(BaseTask):
  def work(self):
    return 'FakeTask'
