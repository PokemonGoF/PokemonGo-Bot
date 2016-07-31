import unittest
import json
from pokemongo_bot.cell_workers import BaseTask

class FakeTask(BaseTask):
    def initialize(self):
        self.foo = 'foo'

    def work(self):
        pass

class FakeTaskWithoutInitialize(BaseTask):
    def work(self):
        pass

class FakeTaskWithoutWork(BaseTask):
    pass

class BaseTaskTest(unittest.TestCase):
    def setUp(self):
        self.bot = {}
        self.config = {}

    def test_initialize_called(self):
        task = FakeTask(self.bot, self.config)
        self.assertIs(task.bot, self.bot)
        self.assertIs(task.config, self.config)
        self.assertEquals(task.foo, 'foo')

    def test_does_not_throw_without_initialize(self):
        FakeTaskWithoutInitialize(self.bot, self.config)

    def test_throws_without_work(self):
        self.assertRaisesRegexp(
            NotImplementedError,
            'Missing "work" method',
            FakeTaskWithoutWork,
            self.bot,
            self.config
        )
