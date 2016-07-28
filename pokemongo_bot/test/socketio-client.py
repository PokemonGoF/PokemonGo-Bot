from socketIO_client import SocketIO, LoggingNamespace, BaseNamespace


def on_events(msg):
    print('received event: ', msg)

if __name__ == "__main__":
    try:
        socketio = SocketIO('localhost', 4000)
        socketio.on('events', on_events)
        while True:
            socketio.wait(seconds=5)

    except (KeyboardInterrupt, SystemExit):
        print "Exiting"
