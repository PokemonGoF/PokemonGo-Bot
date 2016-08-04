import logging

import socketio
from flask import Flask


sio = socketio.Server(async_mode='eventlet', logging=logging.NullHandler)
app = Flask(__name__)

# client asks for data
@sio.on('remote:send_request')
def remote_control(sid, command):
    if not 'account' in command:
        return False
    bot_name = command.pop('account')
    event = 'bot:process_request:{}'.format(bot_name)
    sio.emit(event, data=command)

# sending bot response to client
@sio.on('bot:send_reply')
def request_reply(sid, response):
    event = response.pop('command')
    account = response.pop('account')
    event = "{}:{}".format(event, account)
    sio.emit(event, response)

@sio.on('bot:broadcast')
def bot_broadcast(sid, env):
    event = env.pop('event')
    account = env.pop('account')
    event_name = "{}:{}".format(event, account)
    sio.emit(event_name, data=env['data'])
