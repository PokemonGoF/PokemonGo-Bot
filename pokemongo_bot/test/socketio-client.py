from socketIO_client import SocketIO


def on_location(msg):
    print('received location: {}'.format(msg))

if __name__ == "__main__":
    try:
        socketio = SocketIO('localhost', 4000)
        socketio.on('location', on_location)
        while True:
            socketio.wait(seconds=5)

    except (KeyboardInterrupt, SystemExit):
        print "Exiting"
