import socketio
import logging
from eventlet import wsgi
from flask import Flask, render_template
from pokemongo_bot.event_manager import EventManager
from pokemongo_bot.event_handlers import LoggingHandler

sio = socketio.Server(async_mode='eventlet', logging=logging.NullHandler)
app = Flask(__name__)

event_manager = EventManager()
event_manager.add_handler(LoggingHandler())
event_manager.register_event(
    "websocket_client_connected",
)

@sio.on('bot:broadcast')
def bot_broadcast(sid, env):
    sio.emit(env['event'], data=env['data'])

@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)
