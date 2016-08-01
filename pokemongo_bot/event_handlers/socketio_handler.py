from socketIO_client import SocketIO

from pokemongo_bot.event_manager import EventHandler


class SocketIoHandler(EventHandler):


    def __init__(self, url):
        super(EventHandler, self).__init__()
        self.host, port_str = url.split(':')
        self.port = int(port_str)
        self.sio = SocketIO(self.host, self.port)

    def handle_event(self, event, sender, level, msg, data):
        if msg:
            data['msg'] = unicode(msg.decode('utf-8'))

        self.sio.emit(
            'bot:broadcast',
            {
                'event': event,
                'data': data,
            }
        )
