from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):
    def handle_event(self, event, level, **kwargs):
        # Proper usage of logging module goes here
        print("LOG HANDLER: %s:%s" % (event, kwargs))
