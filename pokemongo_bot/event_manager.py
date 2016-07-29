

class EventNotRegisteredException(Exception):
    pass


class EventMalformedException(Exception):
    pass


class EventHandler(object):
    def __init__(self):
        pass

    def handle_event(self, event, kwargs):
        raise NotImplementedError("Please implement")


class EventManager(object):
    def __init__(self, *handlers):
        self._registered_events = dict()
        self._handlers = handlers or []

    def add_handler(self, event_handler):
        self._handlers.append(event_handler)

    def register_event(self, name, parameters=None):
        self._registered_events[name] = parameters

    def emit(self, event, sender=None, level='info', data={}):
        if not sender:
            raise ArgumentError('Event needs a sender!')

        levels = ['info', 'warning', 'error', 'critical', 'debug']
        if not level in levels:
            raise ArgumentError('Event level needs to be in: {}'.format(levels))

        if event not in self._registered_events:
            raise EventNotRegisteredException("Event %s not registered..." % event)

        # verify params match event
        parameters = self._registered_events[event]
        for k, v in data.iteritems():
            if k not in parameters:
                raise EventMalformedException("Event %s does not require parameter %s" % (event, k))

        # send off to the handlers
        for handler in self._handlers:
            handler.handle_event(event, sender, level, data)
