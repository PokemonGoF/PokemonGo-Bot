from pokemongo_bot.event_manager import EventHandler
from socketIO_client import SocketIO


class SocketIoHandler(EventHandler):


    def __init__(self):
        super(EventHandler, self).__init__()

    def handle_event(self, event, level, **kwargs):
        with SocketIO('localhost', 4000) as sio:
            sio.emit('bot:broadcast', {'event': event, 'data': kwargs})
