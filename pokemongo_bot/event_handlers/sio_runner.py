import threading

import socketio
import eventlet
from eventlet import wsgi
from flask import Flask, render_template

from eventlet import patcher

patcher.monkey_patch(all=True)

sio = socketio.Server(async_mode='eventlet')
app = Flask(__name__)


@app.route('/')
def index():
    """Serve the client-side application."""
    return render_template('index.html')


@sio.on('connect')
def connect(sid, environ):
    print('connect ', sid)


@sio.on('my message')
def message(sid, data):
    print('message ', data)


@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)


class SocketIoRunner(object):
    def __init__(self, listen_address, listen_port):
        self.listen_address = listen_address
        self.listen_port = listen_port
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
        listener = eventlet.listen((self.listen_address, self.listen_port))
        self.server = wsgi.server(listener, self.app)

    def handle_event(self, event, kwargs):
        print("%s:%s" % (event, kwargs))
        sio.emit(event, data=kwargs)




