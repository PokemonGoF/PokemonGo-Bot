# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from socketIO_client import SocketIO

from pokemongo_bot.event_manager import EventHandler


class SocketIoHandler(EventHandler):


    def __init__(self, bot, url):
        self.bot = bot
        self.host, port_str = url.split(':')
        self.port = int(port_str)
        self.sio = SocketIO(self.host, self.port)

    def handle_event(self, event, sender, level, msg, data):
        if msg:
            data['msg'] = msg

        self.sio.emit(
            'bot:broadcast',
            {
                'event': event,
                'account': self.bot.config.username,
                'data': data
            }
        )
