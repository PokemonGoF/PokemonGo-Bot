from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):
    def handle_event(self, event, **kwargs):
        print("LOG HANDLER: %s:%s" % (event, kwargs))
