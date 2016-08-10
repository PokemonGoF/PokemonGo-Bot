# coding: utf-8
from socketIO_client import SocketIO
s = SocketIO('localhost', 4000)
def echo(msg):
    print msg
    
s.on('get_player_info:d.camata@gmail.com', echo)
s.emit('remote:send_request', {'account': 'd.camata@gmail.com', 'name': 'get_player_info'})
s.wait(1)
