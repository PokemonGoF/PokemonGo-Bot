from pokemongo_bot.event_manager import EventHandler
from socketIO_client import SocketIO


class SocketIoHandler(EventHandler):


    def __init__(self, url):
        super(EventHandler, self).__init__()
        self.host, port_str = url.split(':')
        self.port = int(port_str)


    def handle_event(self, event, sender, level, data):
        with SocketIO(self.host, self.port) as sio:
            sio.emit('bot:broadcast', {'event': event, 'data': data})
