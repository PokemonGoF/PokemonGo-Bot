# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from sys import stdout


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

    def __init__(self, limit_output=False, *handlers):
        self._registered_events = dict()
        self._handlers = list(handlers) or []
        self._last_event = None
        self._limit_output = limit_output

    def event_report(self):
        for event, parameters in self._registered_events.iteritems():
            print('-'*80)
            print('Event: {}'.format(event))
            if parameters:
                print('Parameters:')
                for parameter in parameters:
                    print('* {}'.format(parameter))

    def add_handler(self, event_handler):
        self._handlers.append(event_handler)

    def register_event(self, name, parameters=[]):
        self._registered_events[name] = parameters

    def emit(self, event, sender=None, level='info', formatted='', data={}):
        if not sender:
            raise ArgumentError('Event needs a sender!')

        levels = ['info', 'warning', 'error', 'critical', 'debug']
        if not level in levels:
            raise ArgumentError('Event level needs to be in: {}'.format(levels))

        if event not in self._registered_events:
            raise EventNotRegisteredException("Event %s not registered..." % event)

        if self._limit_output:
            if (event == self._last_event) and (event in ["moving_to_fort", "moving_to_lured_fort", "position_update", "moving_to_hunter_target"]):
                stdout.write("\033[1A\033[0K\r")
                stdout.flush()

            if level == "info" and formatted:
                self._last_event = event

        # verify params match event
        parameters = self._registered_events[event]
        if parameters:
            for k, v in data.iteritems():
                if k not in parameters:
                    raise EventMalformedException("Event %s does not require parameter %s" % (event, k))

        formatted_msg = formatted.format(**data)

        # send off to the handlers
        for handler in self._handlers:
            handler.handle_event(event, sender, level, formatted_msg, data)
