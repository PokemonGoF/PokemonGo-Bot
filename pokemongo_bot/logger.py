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
