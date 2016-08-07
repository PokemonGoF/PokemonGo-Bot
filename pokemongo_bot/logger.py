import warnings
import logging


def log(msg, color=None):
    warnings.simplefilter('always', DeprecationWarning)
    message = (
        "Using logger.log is deprecated and will be removed soon. "
        "We recommend that you try to log as little as possible "
        "and use the event system to send important messages "
        "(they become logs and websocket messages) automatically). "
        "If you don't think your message should go to the websocket "
        "server but it's really necessary, use the self.logger variable "
        "inside any class inheriting from BaseTask to log."

def log(string, color='white'):
    color_hex = {
        'red': '91m',
        'green': '92m',
        'yellow': '93m',
        'blue': '94m',
        'cyan': '96m'
    }
    if color not in color_hex:
        print('[{time}] {string}'.format(
            time=time.strftime("%H:%M:%S"),
            string=string.decode('utf-8')
        ))
    else:
        print(
            '[{time}]\033[{color} {string} \033[0m'.format(
                time=time.strftime("%H:%M:%S"),
                color=color_hex[color],
                string=string.decode('utf-8')
            )
        )
    if lcd:
        if string:
            lcd.message(string)
