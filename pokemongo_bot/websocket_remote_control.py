import threading
from socketIO_client import SocketIO, BaseNamespace


class WebsocketRemoteControl(object):


    def __init__(self, bot):
        self.bot = bot
        self.host, port_str = self.bot.config.websocket_server_url.split(':')
        self.port = int(port_str)
        self.sio = SocketIO(self.host, self.port)
        self.sio.on(
            'bot:process_request:{}'.format(self.bot.config.username),
            self.on_remote_command
        )
        self.thread = threading.Thread(target=self.process_messages)

    def start(self):
        self.thread.start()
        return self

    def process_messages(self):
        self.sio.wait()

    def on_remote_command(self, command):
        name = command['name']
        command_handler = getattr(self, name, None)
        if not command_handler or not callable(command_handler):
            self.sio.emit(
                'bot:send_reply',
                {
                    'response': '',
                    'command': 'command_not_found',
                    'account': self.bot.config.username
                }
            )
            return
        if 'args' in command:
            command_handler(*args)
            return
        command_handler()

    def get_player_info(self):
        request = self.bot.api.create_request()
        request.get_player()
        request.get_inventory()
        response_dict = request.call()
        inventory = response_dict['responses'].get('GET_INVENTORY', {})
        player_info = response_dict['responses'].get('GET_PLAYER', {})
        self.sio.emit(
            'bot:send_reply',
            {
                'result': {'inventory': inventory, 'player': player_info},
                'command': 'get_player_info',
                'account': self.bot.config.username
            }
        )
