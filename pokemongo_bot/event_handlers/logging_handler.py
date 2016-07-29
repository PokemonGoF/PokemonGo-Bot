import logging
from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):
    def handle_event(self, event, sender, level, data):
        logger = logging.getLogger(type(sender).__name__)
        message = '{}: {}'.format(event, str(data))
        getattr(logger, level)(message)
