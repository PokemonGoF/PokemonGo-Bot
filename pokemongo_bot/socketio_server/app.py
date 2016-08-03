import logging

import socketio
from flask import Flask


sio = socketio.Server(async_mode='eventlet', logging=logging.NullHandler)
app = Flask(__name__)

# client asks for data
@sio.on('remote:send_request')
def remote_control(sid, command):
    sio.emit('bot:process_request', data=command)

# sending bot response to client
@sio.on('bot:send_reply')
def request_reply(sid, response):
    sio.emit(response['command'], response['response'])

@sio.on('bot:broadcast')
def bot_broadcast(sid, env):
    sio.emit(env['event'], data=env['data'])
