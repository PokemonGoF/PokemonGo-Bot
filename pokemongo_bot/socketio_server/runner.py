import threading
import eventlet
import socketio
import logging
from eventlet import patcher, wsgi
from app import app, sio

patcher.monkey_patch(all=True)

class SocketIoRunner(object):

    def __init__(self, url):
        self.host, port_str = url.split(':')
        self.port = int(port_str)
        self.server = None

        # create the thread object
        self.thread = threading.Thread(target=self._start_listening_blocking)

        # wrap Flask application with socketio's middleware
        self.app = socketio.Middleware(sio, app)

    def start_listening_async(self):
        wsgi.is_accepting = True
        self.thread.start()

    def stop_listening(self):
        wsgi.is_accepting = False

    def _start_listening_blocking(self):
        # deploy as an eventlet WSGI server
        listener = eventlet.listen((self.host, self.port))
        self.server = wsgi.server(listener, self.app, log_output=False, debug=False)
