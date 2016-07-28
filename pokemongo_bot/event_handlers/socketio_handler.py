from pokemongo_bot.event_handlers import sio_runner
from pokemongo_bot.event_manager import EventHandler
from socketIO_client import SocketIO


class SocketIoHandler(EventHandler):

    
    def __init__(self, sio_runner):
        super(EventHandler, self).__init__()

    def handle_event(self, event, kwargs):
        with SocketIO('localhost', 4000) as sio:
            sio.emit('broadcast', {'event': event, 'args': kwargs})
