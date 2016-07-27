from pokemongo_bot.event_handlers import sio_runner
from pokemongo_bot.event_manager import EventHandler



class SocketIoHandler(EventHandler):
    def __init__(self, sio_runner):
        super(EventHandler, self).__init__()

        self.sio_runner = sio_runner

    def handle_event(self, event, kwargs):
        print("SocketIoHandler-%s:%s" % (event, kwargs))
        sio_runner.sio.emit(event, data=kwargs)




