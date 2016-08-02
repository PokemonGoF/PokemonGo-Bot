# __init__.py
from mock import MagicMock

from pokemongo_bot.api_wrapper import ApiWrapper
from pokemongo_bot import PokemonGoBot

class FakeApi(ApiWrapper):
    def __init__(self, return_value=None):
        super(FakeApi, self).__init__()
        self._call = MagicMock(return_value=return_value)

    def _can_call(self):
        return True

    def setApiReturnValue(self, value):
        self._call.return_value = value


class FakeBot(PokemonGoBot):
    def __init__(self):
        self.config = MagicMock()
        self.api = FakeApi()

    def updateConfig(self, conf):
        self.config.__dict__.update(conf)
