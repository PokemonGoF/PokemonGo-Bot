# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import sys

from pokemongo_bot.event_manager import EventHandler


class LoggingHandler(EventHandler):
    EVENT_COLOR_MAP = {
        'api_error':                         'red',
        'badges':                            'blue',
        'bot_exit':                          'red',
        'bot_start':                         'green',
        'buddy_candy_earned':                'green',
        'buddy_candy_fail':                  'red',
        'buddy_keep_active':                 'red',
        'buddy_next_reward':                 'yellow',
        'buddy_not_available':               'red',
        'buddy_pokemon':                     'magenta',
        'buddy_update':                      'blue',
        'buddy_update_fail':                 'red',
        'buddy_reward':                      'green',
        'buddy_walked':                      'yellow',
        'catch_limit':                       'red',
        'catch_log':                         'magenta',
        'config_error':                      'red',
        'egg_already_incubating':            'yellow',
        'egg_hatched':                       'green',
        'egg_hatched_fail':                  'red',
        'eggs_hatched_log':                  'magenta',
        'evolve_log':                        'magenta',
        'future_pokemon_release':            'yellow',
        'incubate':                          'green',
        'incubator_already_used':            'yellow',
        'inventory_full':                    'yellow',
        'item_discard_fail':                 'red',
        'item_discarded':                    'green',
        'next_force_recycle':                'green',
        'force_recycle':                     'green',
        'keep_best_release':                 'green',
        'level_up':                          'green',
        'level_up_reward':                   'green',
        'location_cache_error':              'yellow',
        'location_cache_ignored':            'yellow',
        'login_failed':                      'red',
        'login_log':                         'magenta',
        'login_successful':                  'green',
        'log_stats':                         'magenta',
        'log_hash_stats':                    'magenta',
        'lucky_egg_error':                   'red',
        'move_to_map_pokemon_encounter':     'green',
        'move_to_map_pokemon_fail':          'red',
        'next_egg_incubates':                'yellow',
        'next_sleep':                        'green',
        'next_random_pause':                 'green',
        'next_random_alive_pause':           'green',
        'niantic_warning':                   'magenta',
        'no_pokeballs':                      'red',
        'path_lap_end':                      'green',
        'pokemon_appeared':                  'yellow',
        'pokemon_capture_failed':            'red',
        'pokemon_caught':                    'blue',
        'pokemon_evolved':                   'green',
        'pokemon_evolve_check':              'green',
        'pokemon_fled':                      'red',
        'pokemon_inventory_full':            'red',
        'pokemon_nickname_invalid':          'red',
        'pokemon_not_in_range':              'yellow',
        'pokemon_keep':                      'green',
        'pokemon_release':                   'green',
        'pokemon_upgraded':                  'green',
        'pokemon_vanished':                  'red',
        'pokemon_vip_caught':                'blue',
        'pokestop_empty':                    'yellow',
        'pokestop_log':                      'magenta',
        'pokestop_searching_too_often':      'yellow',
        'rename_pokemon':                    'green',
        'show_best_pokemon':                 'magenta',
        'show_inventory':                    'magenta',
        'skip_evolve':                       'yellow',
        'softban':                           'red',
        'softban_log':                       'magenta',
        'spin_limit':                        'red',
        'spun_pokestop':                     'cyan',
        'threw_berry_failed':                'red',
        'transfer_log':                      'magenta',
        'unknown_spin_result':               'red',
        'unset_pokemon_nickname':            'red',
        'vip_pokemon':                       'red',
        'use_incense':                       'blue',
        'vanish_limit_reached':              'red',
        'move_to_map_pokemon_teleport_to':   'yellow',
        'sniper_teleporting':                'yellow',
        'sniper_error':                      'red',

        'sniper_log':                        'none',
        'arrived_at_cluster':                'none',
        'arrived_at_fort':                   'none',
        'bot_sleep':                         'none',
        'bot_random_pause':                  'none',
        'bot_random_alive_pause':            'none',
        'catchable_pokemon':                 'none',
        'found_cluster':                     'none',
        'incubate_try':                      'none',
        'load_cached_location':              'none',
        'location_found':                    'none',
        'login_started':                     'none',
        'lured_pokemon_found':               'none',
        'move_to_map_pokemon_move_towards':  'none',
        'move_to_map_pokemon_teleport_back': 'none',
        'move_to_map_pokemon_updated_map':   'none',
        'moving_to_fort':                    'none',
        'moving_to_lured_fort':              'none',
        'pokemon_catch_rate':                'none',
        'pokemon_evolve_fail':               'none',
        'pokestop_on_cooldown':              'none',
        'pokestop_out_of_range':             'none',
        'polyline_request':                  'none',
        'position_update':                   'none',
        'path_lap_update':                   'none',
        'set_start_location':                'none',
        'softban_fix':                       'none',
        'softban_fix_done':                  'none',
        'spun_fort':                         'none',
        'threw_berry':                       'none',
        'threw_pokeball':                    'none',
        'used_lucky_egg':                    'none',
        'catch_limit_on':                    'yellow',
        'catch_limit_off':                   'green'
    }
    COLOR_CODE = {
        'gray':    '\033[90m',
        'red':     '\033[91m',
        'green':   '\033[92m',
        'yellow':  '\033[93m',
        'blue':    '\033[94m',
        'magenta': '\033[95m',
        'cyan':    '\033[96m',
        'white':   '\033[97m',
        'none':    '\033[0m'
    }

    def __init__(self, color=True, debug=False):
        self.color = color
        self.debug = debug

    def handle_event(self, event, sender, level, formatted_msg, data):
        if not formatted_msg:
            formatted_msg = str(data)

        if self.color and event in self.EVENT_COLOR_MAP:
            color = self.COLOR_CODE[self.EVENT_COLOR_MAP[event]]
            formatted_msg = '{}{}{}'.format(color, formatted_msg, self.COLOR_CODE['none'])

        if self.debug:
            formatted_msg = '[{}] {}'.format(event, formatted_msg)

        logger = logging.getLogger(type(sender).__name__)
        getattr(logger, level)(formatted_msg.encode(sys.stdout.encoding or sys.getdefaultencoding(), "replace").decode("utf-8", "replace"))
