import ctypes

from sys import stdout, platform as _platform
from datetime import datetime, timedelta

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.tree_config_builder import ConfigException
from pokemongo_bot import inventory

# XP file
import json



class UpdateLiveStats(BaseTask):
    """
    Periodically displays stats about the bot in the terminal and/or in its title.

    Fetching some stats requires making API calls. If you're concerned about the amount of calls
    your bot is making, don't enable this worker.

    Example config :
    {
        "type": "UpdateLiveStats",
        "config": {
            "min_interval": 10,
            "stats": ["login", "uptime", "km_walked", "level_stats", "xp_earned", "xp_per_hour"],
            "terminal_log": true,
            "terminal_title": false
        }
    }

    min_interval : The minimum interval at which the stats are displayed,
                   in seconds (defaults to 120 seconds).
                   The update interval cannot be accurate as workers run synchronously.
    stats : An array of stats to display and their display order (implicitly),
            see available stats below (defaults to []).
    terminal_log : Logs the stats into the terminal (defaults to false).
    terminal_title : Displays the stats into the terminal title (defaults to true).

    Available stats :
    - login : The account login (from the credentials).
    - username : The trainer name (asked at first in-game connection).
    - uptime : The bot uptime.
    - km_walked : The kilometers walked since the bot started.
    - level : The current character's level.
    - level_completion : The current level experience, the next level experience and the completion
                         percentage.
    - level_stats : Puts together the current character's level and its completion.
    - xp_per_hour : The estimated gain of experience per hour.
    - xp_earned : The experience earned since the bot started.
    - stops_visited : The number of visited stops.
    - pokemon_encountered : The number of encountered pokemon.
    - pokemon_caught : The number of caught pokemon.
    - captures_per_hour : The estimated number of pokemon captured per hour.
    - pokemon_released : The number of released pokemon.
    - pokemon_evolved : The number of evolved pokemon.
    - pokemon_unseen : The number of pokemon never seen before.
    - pokemon_stats : Puts together the pokemon encountered, caught, released, evolved and unseen.
    - pokeballs_thrown : The number of thrown pokeballs.
    - stardust_earned : The number of earned stardust since the bot started.
    - stardust_per_hour : The estimated gain of stardust per hour
    - total_stardust : The stardust in possesion of Trainer
    - highest_cp_pokemon : The caught pokemon with the highest CP since the bot started.
    - most_perfect_pokemon : The most perfect caught pokemon since the bot started.
    - location : The location where the player is located.
    - next_egg_hatching : The remaining distance to the next egg hatching (km).
    - hatched_eggs : The number of hatched eggs since the bot started.
    """
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        """
        Initializes the worker.
        :param bot: The bot instance.
        :type bot: PokemonGoBot
        :param config: The task configuration.
        :type config: dict
        """
        super(UpdateLiveStats, self).__init__(bot, config)

        self.next_update = None

        self.min_interval = int(self.config.get('min_interval', 120))
        self.displayed_stats = self.config.get('stats', [])
        self.terminal_log = bool(self.config.get('terminal_log', False))
        self.terminal_title = bool(self.config.get('terminal_title', True))

        self.bot.event_manager.register_event('log_stats', parameters=('stats', 'stats_raw'))

        # init xp_per_level
        self.xp_per_level = None
        # If xp_level file exists, load variables from json
        # file name should not be hard coded either
        xpfile = "data/xp_per_level.json"
        try:
            with open(xpfile, 'rb') as data:
                self.xp_per_level = json.load(data)
        except (ValueError, IOError):
            # log somme warning message
            self.emit_event(
                'log_stats',
                level='info',
                formatted="Unable to read XP level file"
            )
            # load default valuesto supplement unknown current_level_xp
            self.xp_per_level = [[1, 0, 0],
                [2, 1000, 1000],
                [3, 2000, 3000],
                [4, 3000, 6000],
                [5, 4000, 10000],
                [6, 5000, 15000],
                [7, 6000, 21000],
                [8, 7000, 28000],
                [9, 8000, 36000],
                [10, 9000, 45000],
                [11, 10000, 55000],
                [12, 10000, 65000],
                [13, 10000, 75000],
                [14, 10000, 85000],
                [15, 15000, 100000],
                [16, 20000, 120000],
                [17, 20000, 140000],
                [18, 20000, 160000],
                [19, 25000, 185000],
                [20, 25000, 210000],
                [21, 50000, 260000],
                [22, 75000, 335000],
                [23, 100000, 435000],
                [24, 125000, 560000],
                [25, 150000, 710000],
                [26, 190000, 900000],
                [27, 200000, 1100000],
                [28, 250000, 1350000],
                [29, 300000, 1650000],
                [30, 350000, 2000000],
                [31, 500000, 2500000],
                [32, 500000, 3000000],
                [33, 750000, 3750000],
                [34, 1000000, 4750000],
                [35, 1250000, 6000000],
                [36, 1500000, 7500000],
                [37, 2000000, 9500000],
                [38, 2500000, 12000000],
                [39, 3000000, 15000000],
                [40, 5000000, 20000000]
            ]

    def initialize(self):
        pass

    def work(self):
        """
        Displays the stats if necessary.
        :return: Always returns WorkerResult.SUCCESS.
        :rtype: WorkerResult
        """
        if not self._should_display():
            return WorkerResult.SUCCESS

        player_stats = inventory.player().player_stats
        line = self._get_stats_line(self._get_stats(player_stats))
        # If line is empty, it couldn't be generated.
        if not line:
            return WorkerResult.SUCCESS

        if self.terminal_title:
            self._update_title(line, _platform)

        if self.terminal_log:
            self._log_on_terminal(line)
        return WorkerResult.SUCCESS

    def _should_display(self):
        """
        Returns a value indicating whether the stats should be displayed.
        :return: True if the stats should be displayed; otherwise, False.
        :rtype: bool
        """
        if not self.terminal_title and not self.terminal_log or not self.displayed_stats:
            return False
        return self.next_update is None or datetime.now() >= self.next_update

    def _compute_next_update(self):
        """
        Computes the next update datetime based on the minimum update interval.
        :return: Nothing.
        :rtype: None
        """
        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)

    def _log_on_terminal(self, stats):
        """
        Logs the stats into the terminal using an event.
        :param stats: The stats to display.
        :type stats: string
        :return: Nothing.
        :rtype: None
        """
        self.emit_event(
            'log_stats',
            formatted="{stats}",
            data={
                'stats': stats,
                'stats_raw': self._get_stats(inventory.player().player_stats)
            }
        )
        self._compute_next_update()

    def _update_title(self, title, platform):
        """
        Updates the window title using different methods, according to the given platform.
        :param title: The new window title.
        :type title: string
        :param platform: The platform string.
        :type platform: string
        :return: Nothing.
        :rtype: None
        :raise: RuntimeError: When the given platform isn't supported.
        """

        try:
            if platform == "linux" or platform == "linux2" or platform == "cygwin":
                stdout.write("\x1b]2;{}\x07".format(title))
                stdout.flush()
            elif platform == "darwin" or platform == "freebsd10":
                stdout.write("\033]0;{}\007".format(title))
                stdout.flush()
            elif platform == "win32":
                ctypes.windll.kernel32.SetConsoleTitleA(title.encode())
            else:
                self.bot.logger.warn("Unable to set window title. OS {} not supported.".format(platform))
        except AttributeError:
            self.emit_event(
                'log_stats',
                level='error',
                formatted="Unable to write window title"
            )
            self.terminal_title = False

        self._compute_next_update()

    def _get_stats(self, player_stats):
        """ Some data """
        metrics = self.bot.metrics
        metrics.capture_stats()
        runtime = metrics.runtime()
        login = self.bot.config.username
        player_data = self.bot.player_data
        username = player_data.get('username', '?')
        distance_travelled = metrics.distance_travelled()
        current_level = int(player_stats.get('level', 0))
        prev_level_xp = int(self.xp_per_level[current_level - 1][2])
        next_level_xp = int(player_stats.get('next_level_xp', 0))
        experience = int(player_stats.get('experience', 0))
        current_level_xp = experience - prev_level_xp
        whole_level_xp = next_level_xp - prev_level_xp
        level_completion_percentage = int((current_level_xp * 100) / whole_level_xp)
        experience_per_hour = int(metrics.xp_per_hour())
        # Calculate est time to level
        remaining_xp = next_level_xp - current_level_xp
        # eample; 30_000 xp remaining 3000 xp/h => 10h till level
        if experience_per_hour > 0:
            ttl = (float(remaining_xp) / float(experience_per_hour))
            hours = int(ttl)
            minutes = int((ttl - hours) * 60)
            if hours > 24:
                days = hours / 24
                hours = hours % 24
                time_to_level = "%s days %s hours %s minutes" % (days, hours, minutes)
            else:
                time_to_level = "%s hours %s minutes" % (hours, minutes)
        else:
            time_to_level = "Unknown"
        xp_earned = metrics.xp_earned()
        stops_visited = metrics.visits['latest'] - metrics.visits['start']
        pokemon_encountered = metrics.num_encounters()
        pokemon_caught = metrics.num_captures()
        captures_per_hour = int(metrics.captures_per_hour())
        pokemon_released = metrics.releases
        pokemon_evolved = metrics.num_evolutions()
        pokemon_unseen = metrics.num_new_mons()
        pokeballs_thrown = metrics.num_throws()
        dust_per_hour = int(metrics.stardust_per_hour())
        total_stardust = int(metrics.total_stardust())
        stardust_earned = metrics.earned_dust()
        highest_cp_pokemon = metrics.highest_cp['desc']
        if not highest_cp_pokemon:
            highest_cp_pokemon = "None"
        most_perfect_pokemon = metrics.most_perfect['desc']
        if not most_perfect_pokemon:
            most_perfect_pokemon = "None"
        next_egg_hatching = metrics.next_hatching_km(0)
        hatched_eggs = metrics.hatched_eggs(0)

        # Create stats strings.
        available_stats = {
            'login': login,
            'username': username,
            'uptime': '{}'.format(runtime),
            'km_walked': distance_travelled,
            'level': current_level,
            'experience': experience,
            'current_level_xp': current_level_xp,
            'whole_level_xp': whole_level_xp,
            'level_completion_percentage': level_completion_percentage,
            'xp_per_hour': experience_per_hour,
            'xp_earned': xp_earned,
            'time_to_level': time_to_level,
            'stops_visited': stops_visited,
            'pokemon_encountered': pokemon_encountered,
            'pokemon_caught': pokemon_caught,
            'captures_per_hour': captures_per_hour,
            'pokemon_released': pokemon_released,
            'pokemon_evolved': pokemon_evolved,
            'pokemon_unseen': pokemon_unseen,
            'pokeballs_thrown': pokeballs_thrown,
            'stardust_earned': stardust_earned,
            'stardust_per_hour': dust_per_hour,
            'total_stardust' : total_stardust,
            'highest_cp_pokemon': highest_cp_pokemon,
            'most_perfect_pokemon': most_perfect_pokemon,
            'location': [self.bot.position[0], self.bot.position[1]],
            'next_egg_hatching': float(next_egg_hatching),
            'hatched_eggs': hatched_eggs
        }

        return available_stats

    def _get_stats_line(self, player_stats):
        """
        Generates a stats string with the given player stats according to the configuration.
        :return: A string containing human-readable stats, ready to be displayed.
        :rtype: string
        """
        # No player stats available, won't be able to gather all informations.
        if player_stats is None:
            return ''

        # Create stats strings.
        available_stats = {
            'login': player_stats['login'],
            'username': player_stats['username'],
            'uptime': 'Uptime : {}'.format(player_stats['uptime']),
            'km_walked': '{:,.2f}km walked'.format(player_stats['km_walked']),
            'level': 'Level {}'.format(player_stats['level']),
            'level_completion': '{:,} / {:,} XP ({}%)'.format(
                player_stats['current_level_xp'], player_stats['whole_level_xp'],
                player_stats['level_completion_percentage']),
            'level_stats': 'Level {} ({:,} / {:,}, {}%)'.format(
                player_stats['level'], player_stats['current_level_xp'],
                player_stats['whole_level_xp'], player_stats['level_completion_percentage']),
            'xp_per_hour': '{:,} XP/h'.format(player_stats['xp_per_hour']),
            'xp_earned': '+{:,} XP'.format(player_stats['xp_earned']),
            'time_to_level': 'TTL: {}'.format(player_stats['time_to_level']),
            'stops_visited': 'Visited {:,} stops'.format(player_stats['stops_visited']),
            'pokemon_encountered': 'Encountered {:,} pokemon'.format(player_stats['pokemon_encountered']),
            'pokemon_caught': 'Caught {:,} pokemon'.format(player_stats['pokemon_caught']),
            'captures_per_hour': '{:,} pokemon/h'.format(player_stats['captures_per_hour']),
            'pokemon_released': 'Released {:,} pokemon'.format(player_stats['pokemon_released']),
            'pokemon_evolved': 'Evolved {:,} pokemon'.format(player_stats['pokemon_evolved']),
            'pokemon_unseen': 'Encountered {} new pokemon'.format(player_stats['pokemon_unseen']),
            'pokemon_stats': 'Encountered {:,} pokemon, {:,} caught, {:,} released, {:,} evolved, {} never seen before'.format(
                player_stats['pokemon_encountered'], player_stats['pokemon_caught'],
                player_stats['pokemon_released'], player_stats['pokemon_evolved'], player_stats['pokemon_unseen']
            ),
            'pokeballs_thrown': 'Threw {:,} pokeballs'.format(player_stats['pokeballs_thrown']),
            'stardust_earned': 'Earned {:,} Stardust'.format(player_stats['stardust_earned']),
            'stardust_per_hour': '{:,} Stardust/h'.format(player_stats['stardust_per_hour']),
            'total_stardust': 'Total Stardust: {:,}'.format(player_stats['total_stardust']),
            'highest_cp_pokemon': 'Highest CP pokemon : {}'.format(player_stats['highest_cp_pokemon']),
            'most_perfect_pokemon': 'Most perfect pokemon : {}'.format(player_stats['most_perfect_pokemon']),
            'location': 'Location : ({}, {})'.format(*player_stats['location']),
            'next_egg_hatching': 'Next egg hatches in : {:.2f} km'.format(player_stats['next_egg_hatching']),
            'hatched_eggs': 'Hatched {} eggs.'.format(player_stats['hatched_eggs'])
        }

        def get_stat(stat):
            """
            Fetches a stat string from the available stats dictionary.
            :param stat: The stat name.
            :type stat: string
            :return: The generated stat string.
            :rtype: string
            :raise: ConfigException: When the provided stat string isn't in the available stats
            dictionary.
            """
            if stat not in available_stats:
                raise ConfigException("stat '{}' isn't available for displaying".format(stat))
            return available_stats[stat]

        # Map stats the user wants to see to available stats and join them with pipes.
        line = ' | '.join(map(get_stat, self.displayed_stats))

        return line
