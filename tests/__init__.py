# __init__.py
from mock import MagicMock

from pokemongo_bot.event_manager import EventManager
from pokemongo_bot.api_wrapper import ApiWrapper, ApiRequest
from pokemongo_bot import PokemonGoBot

import json

def get_fake_conf():
    class ConfObj:
        pass

    conf_dict = json.load(open('configs/auth.json.example'))
    conf_dict.update(json.load(open('configs/config.json.example')))
    conf_obj = ConfObj()
    for key, value in conf_dict.items():
        setattr(conf_obj, key, value)

    return conf_obj


class FakeApi(ApiWrapper):
    def __init__(self):
        super(FakeApi, self).__init__(get_fake_conf())

    def create_request(self, return_value='mock return'):
        request = ApiWrapper.create_request(self)
        request.can_call = MagicMock(return_value=True)
        request._call = MagicMock(return_value=return_value)
        return request

class FakeBot(PokemonGoBot):
    def __init__(self):
        self.config = MagicMock(websocket_server_url=False, show_events=False)
        self.api = FakeApi()
        self.event_manager = EventManager(None)
        self._setup_event_system(None)

    def updateConfig(self, conf):
        self.config.__dict__.update(conf)
