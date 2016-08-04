#!/usr/bin/env python
# -*- coding: utf-8 -

import argparse

from pokemongo_bot.socketio_server.runner import SocketIoRunner


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        help="Host for the websocket",
        type=str,
        default='localhost'
    )
    parser.add_argument(
        "--port",
        help="Port for the websocket",
        type=int,
        default=4000
    )
    config = parser.parse_known_args()[0]

    s = SocketIoRunner("{}:{}".format(config.host, config.port))
    s._start_listening_blocking()
