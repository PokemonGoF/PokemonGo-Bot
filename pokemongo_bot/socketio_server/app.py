import logging

import socketio
from flask import Flask

from pokemongo_bot.event_handlers import LoggingHandler
from pokemongo_bot.event_manager import EventManager

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
