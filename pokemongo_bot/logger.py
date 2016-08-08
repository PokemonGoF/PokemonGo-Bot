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

    )

    logger = logging.getLogger('generic')
    logger.info(msg)
    warnings.warn(message, DeprecationWarning)

class ColorizedLogFormatter(logging.Formatter):
    RESET_SEQ = '\033[0m'
    COLOR_SEQ = '\033[1;%s'

    color_hex = {
        'ERROR': '91m',
        'red': '91m',
        'DEBUG': '92m',
        'green': '92m',
        'WARNING': '93m',
        'yellow': '93m',
        'blue': '94m',
        'INFO': '96m',
        'cyan': '96m',
        'VERBOSE': '37m',
        'white': '37m'
    }

    fmt='%(asctime)s [%(name)10s] [%(levelname)s] %(message)s'
#    fmt = '%(asctime)s %(message)s'
    datefmt = '%H:%M:%S'

    def __init__(self, fmt=fmt, datefmt=datefmt):
        super(ColorizedLogFormatter, self).__init__(fmt, datefmt)

    def get_color(self, record):
        # We default to white
        color = ColorizedLogFormatter.color_hex.get(getattr(record, 'color', None), None) or \
                self.color_hex.get(record.levelname, ColorizedLogFormatter.color_hex['white'])
        return color

    def format(self, record):
        level = record.levelname
        color = self.get_color(record)
        record.msg = '{color}{message}{reset}'.format(color=ColorizedLogFormatter.COLOR_SEQ % (color), message=record.msg, reset=ColorizedLogFormatter.RESET_SEQ)
#        record.msg = '{color}{message}'.format(color='', message=record.msg)
        result = logging.Formatter.format(self, record)
        return result

# In some cases, we need colorized logging without calling functions like
# logger.error(...). The following lines add this capability
WHITE_LEVELV_NUM = 21
GREEN_LEVELV_NUM = 22
YELLOW_LEVELV_NUM = 23
BLUE_LEVELV_NUM = 24
CYAN_LEVELV_NUM = 25
RED_LEVELV_NUM = 26
def custom_logging_level_handler(self, level, message, args, kwargs):
    if self.isEnabledFor(level):
        self._log(level, message, args, **kwargs)
def white(self, message, *args, **kwargs):
    return custom_logging_level_handler(self, WHITE_LEVELV_NUM, message, args, kwargs)
def green(self, message, *args, **kwargs):
    return custom_logging_level_handler(self, GREEN_LEVELV_NUM, message, args, kwargs)
def yellow(self, message, *args, **kwargs):
    return custom_logging_level_handler(self, YELLOW_LEVELV_NUM, message, args, kwargs)
def blue(self, message, *args, **kwargs):
    return custom_logging_level_handler(self, BLUE_LEVELV_NUM, message, args, kwargs)
def cyan(self, message, *args, **kwargs):
    return custom_logging_level_handler(self, CYAN_LEVELV_NUM, message, args, kwargs)
def red(self, message, *args, **kwargs):
    return custom_logging_level_handler(self, RED_LEVELV_NUM, message, args, kwargs)
def colorized(self, level, message, color, *args, **kwargs):
    extra = {'color': color}
    kwargs['extra'] = extra
    return custom_logging_level_handler(self, level, message, args, kwargs)

logging.Logger.white = white
logging.addLevelName(WHITE_LEVELV_NUM, 'white')
logging.Logger.green = green
logging.addLevelName(GREEN_LEVELV_NUM, 'green')
logging.Logger.yellow = yellow
logging.addLevelName(YELLOW_LEVELV_NUM, 'yellow')
logging.Logger.blue = blue
logging.addLevelName(BLUE_LEVELV_NUM, 'blue')
logging.Logger.cyan = cyan
logging.addLevelName(CYAN_LEVELV_NUM, 'cyan')
logging.Logger.red = red
logging.addLevelName(RED_LEVELV_NUM, 'red')
logging.Logger.colorized = colorized
