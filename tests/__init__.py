# __init__.py
from mock import MagicMock

from pokemongo_bot.api_wrapper import ApiWrapper, ApiRequest
from pokemongo_bot import PokemonGoBot

class FakeApi(ApiWrapper):
    def create_request(self, return_value='mock return'):
        request = ApiWrapper.create_request(self)
        request.can_call = MagicMock(return_value=True)
        request._call = MagicMock(return_value=return_value)
        return request

class FakeBot(PokemonGoBot):
    def __init__(self):
        self.config = MagicMock()
        self.api = FakeApi()

    def updateConfig(self, conf):
        self.config.__dict__.update(conf)
