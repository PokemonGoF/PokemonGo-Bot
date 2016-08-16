# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from pokemongo_bot.event_manager import EventHandler


class ColoredLoggingHandler(EventHandler):
    EVENT_COLOR_MAP = {
        'api_error':                         'red',
        'bot_exit':                          'red',
        'bot_start':                         'green',
        'config_error':                      'red',
        'egg_already_incubating':            'yellow',
        'egg_hatched':                       'green',
        'future_pokemon_release':            'yellow',
        'incubate':                          'green',
        'incubator_already_used':            'yellow',
        'inventory_full':                    'yellow',
        'item_discard_fail':                 'red',
        'item_discarded':                    'green',
        'keep_best_release':                 'green',
        'level_up':                          'green',
        'level_up_reward':                   'green',
        'location_cache_error':              'yellow',
        'location_cache_ignored':            'yellow',
        'login_failed':                      'red',
        'login_successful':                  'green',
        'lucky_egg_error':                   'red',
        'move_to_map_pokemon_encounter':     'green',
        'move_to_map_pokemon_fail':          'red',
        'next_egg_incubates':                'yellow',
        'next_sleep':                        'green',
        'no_pokeballs':                      'red',
        'pokemon_appeared':                  'yellow',
        'pokemon_capture_failed':            'red',
        'pokemon_caught':                    'blue',
        'pokemon_evolved':                   'green',
        'pokemon_fled':                      'red',
        'pokemon_inventory_full':            'red',
        'pokemon_nickname_invalid':          'red',
        'pokemon_not_in_range':              'yellow',
        'pokemon_release':                   'green',
        'pokemon_vanished':                  'red',
        'pokestop_empty':                    'yellow',
        'pokestop_searching_too_often':      'yellow',
        'rename_pokemon':                    'green',
        'skip_evolve':                       'yellow',
        'softban':                           'red',
        'spun_pokestop':                     'cyan',
        'threw_berry_failed':                'red',
        'unknown_spin_result':               'red',
        'unset_pokemon_nickname':            'red',
        'vip_pokemon':                       'red',

        # event names for 'white' still here to remember that these events are already determined its color.
        'arrived_at_cluster':                'white',
        'arrived_at_fort':                   'white',
        'bot_sleep':                         'white',
        'catchable_pokemon':                 'white',
        'found_cluster':                     'white',
        'incubate_try':                      'white',
        'load_cached_location':              'white',
        'location_found':                    'white',
        'login_started':                     'white',
        'lured_pokemon_found':               'white',
        'move_to_map_pokemon_move_towards':  'white',
        'move_to_map_pokemon_teleport_back': 'white',
        'move_to_map_pokemon_updated_map':   'white',
        'moving_to_fort':                    'white',
        'moving_to_lured_fort':              'white',
        'pokemon_catch_rate':                'white',
        'pokemon_evolve_fail':               'white',
        'pokestop_on_cooldown':              'white',
        'pokestop_out_of_range':             'white',
        'polyline_request':                  'white',
        'position_update':                   'white',
        'set_start_location':                'white',
        'softban_fix':                       'white',
        'softban_fix_done':                  'white',
        'spun_fort':                         'white',
        'threw_berry':                       'white',
        'threw_pokeball':                    'white',
        'used_lucky_egg':                    'white',
        'save_spawn':                        'white'
    }
    CONTINUOUS_EVENT_NAMES = [
        'catchable_pokemon',
        'moving_to_lured_fort',
        'spun_fort'
    ]
    COLOR_CODE = {
        'gray':    '\033[90m',
        'red':     '\033[91m',
        'green':   '\033[92m',
        'yellow':  '\033[93m',
        'blue':    '\033[94m',
        'magenta': '\033[95m',
        'cyan':    '\033[96m',
        'white':   '\033[97m',
        'reset':   '\033[0m'
    }

    def handle_event(self, event, sender, level, formatted_msg, data):
        logger = logging.getLogger(type(sender).__name__)

        color = self.COLOR_CODE['white']
        if event in self.EVENT_COLOR_MAP:
            color = self.COLOR_CODE[self.EVENT_COLOR_MAP[event]]
        if event == 'egg_hatched' and data.get('pokemon', 'error') == 'error':
            color = self.COLOR_CODE['red']
        formatted_msg = '{}{}{}'.format(color, formatted_msg, self.COLOR_CODE['reset'])

        if formatted_msg:
            message = "[{}] {}".format(event, formatted_msg)
        else:
            message = '{}: {}'.format(event, str(data))
        getattr(logger, level)(message)
