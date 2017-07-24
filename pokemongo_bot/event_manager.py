# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from sys import stdout

from datetime import datetime, timedelta
import time
import json
import os


from pokemongo_bot.base_dir import _base_dir


class FileIOException(Exception):
    pass


class EventNotRegisteredException(Exception):
    pass


class EventMalformedException(Exception):
    pass


class EventHandler(object):

    def __init__(self):
        pass

    def handle_event(self, event, kwargs):
        raise NotImplementedError("Please implement")

        
class Event(object):
    """
    Representation of an event.
    """
    def __init__(self, event, sender=None, level='info', formatted='', data={}):
        """
        Representation of an Event
        :return: An Event
        :rtype: Event
        """
        t = datetime.today()
        self.timestamp = t.strftime('%Y-%m-%d %H:%M:%S')
        self.event = str(event).encode('ascii', 'xmlcharrefreplace')
        if sender==None:
            self.sender = sender
        else:
            self.sender = str(sender).encode('ascii', 'xmlcharrefreplace')
        
        self.level = str(level).encode('ascii', 'xmlcharrefreplace')

        #Fixing issue 6123 for gym names that are in utf format.
        self.formatted = str(formatted).encode('utf-8', 'ignore').decode('utf-8')
        self.formatted = str(formatted).encode('ascii', 'xmlcharrefreplace')
        
        self.data = str(data).encode('ascii', 'xmlcharrefreplace')
        self.friendly_msg = ""
        
        if not formatted:
            self.friendly_msg = self.data 
        else:
            #Format the data
            self.friendly_msg = formatted.format(**data)
            
    def __str__(self):
        return self.timestamp + ": [" + str(self.event) + "] " + str(self.data)
        

class Events(object):
    def __init__(self, bot):
        self._events = []
        self.MaxEventlog = 50
        self.bot = bot
        if bot==None:
            self._username = "TESTBUILD"
        else:
            self._username = self.bot.config.username
        #Hardcoded to avoid the file is being flooded on disk
        self._write_debug = False

    def retrieve_data(self):
        return self._events

    def get(self, number):
        return self._events[number]

    def all(self):
        return list(self._data.values())

    def remove_event_by_num(self, number):
        del self._events[number]


    def add_event(self, event):
        #Do not log anything on disk  when in Jenkins test build
        if self._username == "TESTBUILD":
            return

        if event.level=="debug" and self._write_debug==False:
            return
        else:
            self._events.append(event)
        #Check if we exceed the max log entries
        if len(self._events) > self.MaxEventlog:
            self.remove_event_by_num(0)
        #Write file to disk
        self.update_web_event()
    
    def init_event_outfile(self):
        web_event = os.path.join(_base_dir, "web", "events-%s.json" % self._username)

        if not os.path.exists(web_event):
            self.bot.logger.info('No events file %s found. Creating a new one' % web_event)

            json_events = []

            with open(web_event, "w") as outfile:
                json.dump(json_events, outfile)

    def update_web_event(self):
        web_event = os.path.join(_base_dir, "web", "events-%s.json" % self._username)

        if not os.path.exists(web_event):
            self.init_event_outfile()

        json_events = self.jsonify_events()
        #self.bot.logger.info('####### Writing %s' % json_events)

        try:
            with open(web_event, "w") as outfile:
                json.dump(json_events, outfile)
        except (IOError, ValueError) as e:
            self.bot.logger.info('[x] Error while opening events file for write: %s' % e, 'red')
        except:
            raise FileIOException("Unexpected error writing to {}".web_event)

    def jsonify_events(self):
        json_events = []
        for event in self._events:
            json_events.append({"event": {"timestamp": event.timestamp, "friendly_msg": event.friendly_msg, "event": event.event, "level": event.level, "formatted": event.formatted, "data": event.data}})
        return json_events
        
        
class EventManager(object):

    def __init__(self, bot ,limit_output=False, *handlers):


        self._registered_events = dict()
        self._handlers = list(handlers) or []
        self._last_event = None
        self._limit_output = limit_output
        self.bot = bot
        self._EventLog = Events(self.bot)

        
        
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
        
        #Log the event in the event_log
        l_event = Event(event, sender, level, formatted, data) 
        self._EventLog.add_event(l_event)
