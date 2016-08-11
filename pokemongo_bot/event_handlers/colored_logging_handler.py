# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
import sys
import struct

from pokemongo_bot.event_manager import EventHandler

class ColoredLoggingHandler(EventHandler):
    EVENT_COLOR_MAP = {
        'api_error':                        'red',
        'bot_exit':                         'red',
        'bot_start':                        'green',
        'config_error':                     'red',
        'egg_already_incubating':           'yellow',
        'egg_hatched':                      'green',
        'future_pokemon_release':           'yellow',
        'incubate':                         'green',
        'incubator_already_used':           'yellow',
        'inventory_full':                   'yellow',
        'item_discard_fail':                'red',
        'item_discarded':                   'green',
        'keep_best_release':                'green',
        'level_up':                         'green',
        'level_up_reward':                  'green',
        'location_cache_error':             'yellow',
        'location_cache_ignored':           'yellow',
        'login_failed':                     'red',
        'login_successful':                 'green',
        'lucky_egg_error':                  'red',
        'move_to_map_pokemon_encounter':    'green',
        'move_to_map_pokemon_fail':         'red',
        'next_egg_incubates':               'yellow',
        'next_sleep':                       'green',
        'no_pokeballs':                     'red',
        'pokemon_appeared':                 'yellow',
        'pokemon_capture_failed':           'red',
        'pokemon_caught':                   'blue',
        'pokemon_evolved':                  'green',
        'pokemon_fled':                     'red',
        'pokemon_inventory_full':           'red',
        'pokemon_nickname_invalid':         'red',
        'pokemon_not_in_range':             'yellow',
        'pokemon_release':                  'green',
        'pokemon_vanished':                 'red',
        'pokestop_empty':                   'yellow',
        'pokestop_searching_too_often':     'yellow',
        'rename_pokemon':                   'green',
        'skip_evolve':                      'yellow',
        'softban':                          'red',
        'spun_pokestop':                    'cyan',
        'threw_berry_failed':               'red',
        'unknown_spin_result':              'red',
        'unset_pokemon_nickname':           'red',
        'vip_pokemon':                      'red',

        # event names for 'white' still here to remember that these events are already determined its color.
        'arrived_at_cluster':                   'white',
        'arrived_at_fort':                      'white',
        'bot_sleep':                            'white',
        'catchable_pokemon':                    'white',
        'found_cluster':                        'white',
        'incubate_try':                         'white',
        'load_cached_location':                 'white',
        'location_found':                       'white',
        'login_started':                        'white',
        'lured_pokemon_found':                  'white',
        'move_to_map_pokemon_move_towards':     'white',
        'move_to_map_pokemon_teleport_back':    'white',
        'move_to_map_pokemon_updated_map':      'white',
        'moving_to_fort':                       'white',
        'moving_to_lured_fort':                 'white',
        'pokemon_catch_rate':                   'white',
        'pokestop_on_cooldown':                 'white',
        'pokestop_out_of_range':                'white',
        'polyline_request':                     'white',
        'position_update':                      'white',
        'set_start_location':                   'white',
        'softban_fix':                          'white',
        'softban_fix_done':                     'white',
        'spun_fort':                            'white',
        'threw_berry':                          'white',
        'threw_pokeball':                       'white',
        'used_lucky_egg':                       'white'
    }
    CONTINUOUS_EVENT_NAMES = [
        'catchable_pokemon',
        'moving_to_lured_fort',
        'spun_fort'
    ]
    COLOR_CODE = {
        'red':      '91',
        'green':    '92',
        'yellow':   '93',
        'blue':     '94',
        'cyan':     '96'
    }

    def __init__(self):
        self._last_event = None
        try:
            # this `try ... except` is for ImportError on Windows
            import fcntl
            import termios
            self._ioctl = fcntl.ioctl
            self._TIOCGWINSZ = termios.TIOCGWINSZ
        except ImportError:
            self._ioctl = None
            self._TIOCGWINSZ = None

    def handle_event(self, event, sender, level, formatted_msg, data):
        # Prepare message string
        message = None
        if formatted_msg:
            try:
                message = formatted_msg.decode('utf-8')
            except UnicodeEncodeError:
                message = formatted_msg
        else:
            message = '{}'.format(str(data))

        # Replace message if necessary
        if event == 'catchable_pokemon':
            message = 'Something rustles nearby!'

        # Truncate previous line if same event continues
        if event in ColoredLoggingHandler.CONTINUOUS_EVENT_NAMES and self._last_event == event and sys.stdout.isatty():
            # Filling with "' ' * terminal_width" in order to completely clear last line
            terminal_width = self._terminal_width()
            if terminal_width:
                sys.stdout.write('\r{}\r'.format(' ' * terminal_width))
            else:
                sys.stdout.write('\r')
        else:
            sys.stdout.write("\n")

        color_name = None
        if event in ColoredLoggingHandler.EVENT_COLOR_MAP:
            color_name = ColoredLoggingHandler.EVENT_COLOR_MAP[event]

        # Change color if necessary
        if event == 'egg_hatched' and data.get('pokemon', 'error') == 'error':
            # `egg_hatched` event will be dispatched in both cases: hatched pokemon info is successfully taken or not.
            # change color from 'green' to 'red' in case of error.
            color_name = 'red'

        if color_name in ColoredLoggingHandler.COLOR_CODE:
            sys.stdout.write(
                '[{time}] \033[{color}m{message}\033[0m'.format(
                    time=time.strftime("%H:%M:%S"),
                    color=ColoredLoggingHandler.COLOR_CODE[color_name],
                    message=message
                )
            )
        else:
            sys.stdout.write('[{time}] {message}'.format(
                time=time.strftime("%H:%M:%S"),
                message=message
            ))

        sys.stdout.flush()
        self._last_event = event

    def _terminal_width(self):
        if self._ioctl is None or self._TIOCGWINSZ is None:
            return None

        h, w, hp, wp = struct.unpack(str('HHHH'),
            self._ioctl(0, self._TIOCGWINSZ,
            struct.pack(str('HHHH'), 0, 0, 0, 0)))
        return w
