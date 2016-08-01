# __init__.py
from mock import MagicMock

from pgoapi import PGoApi
from pokemongo_bot.api_wrapper import ApiWrapper
from pokemongo_bot.event_manager import EventManager
from pokemongo_bot import PokemonGoBot

class FakeApi(ApiWrapper):
    def __init__(self, return_value=None):
        super(FakeApi, self).__init__(PGoApi())
        self._api.call = MagicMock(return_value=return_value)

    def _can_call(self):
        return True

    def setApiReturnValue(self, value):
        self._api.call.return_value = value


class FakeBot(PokemonGoBot):
    def __init__(self):
        self.config = MagicMock(websocket_server_url=False)
        self.api = FakeApi()
        self.event_manager = EventManager()
        self._setup_event_system()

    def updateConfig(self, conf):
        self.config.__dict__.update(conf)
