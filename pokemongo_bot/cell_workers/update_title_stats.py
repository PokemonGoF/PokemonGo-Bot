import ctypes
from sys import stdout, platform as _platform
from datetime import datetime, timedelta

from pokemongo_bot.cell_workers.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.tree_config_builder import ConfigException

class UpdateTitleStats(BaseTask):
    """
    Periodically updates the terminal title to display stats about the bot.

    Fetching some stats requires making API calls. If you're concerned about the amount of calls
    your bot is making, don't enable this worker.

    Example config :
    {
        "type": "UpdateTitleStats",
        "config": {
            "min_interval": 10,
            "stats": ["uptime", "km_walked", "level_stats", "xp_earned", "xp_per_hour"]
        }
    }

    Available stats :
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
    - pokemon_released : The number of released pokemon.
    - pokemon_evolved : The number of evolved pokemon.
    - pokemon_unseen : The number of pokemon never seen before.
    - pokemon_stats : Puts together the pokemon encountered, caught, released, evolved and unseen.
    - pokeballs_thrown : The number of thrown pokeballs.
    - stardust_earned : The number of earned stardust since the bot started.
    - highest_cp_pokemon : The caught pokemon with the highest CP since the bot started.
    - most_perfect_pokemon : The most perfect caught pokemon since the bot started.

    min_interval : The minimum interval at which the title is updated,
                   in seconds (defaults to 10 seconds).
                   The update interval cannot be accurate as workers run synchronously.
    stats : An array of stats to display and their display order (implicitly),
            see available stats above.
    """

    DEFAULT_MIN_INTERVAL = 10
    DEFAULT_DISPLAYED_STATS = []

    def __init__(self, bot, config):
        """
        Initializes the worker.
        :param bot: The bot instance.
        :type bot: PokemonGoBot
        :param config: The task configuration.
        :type config: dict
        """
        super(UpdateTitleStats, self).__init__(bot, config)

        self.next_update = None
        self.min_interval = self.DEFAULT_MIN_INTERVAL
        self.displayed_stats = self.DEFAULT_DISPLAYED_STATS

        self._process_config()

    def initialize(self):
        pass

    def work(self):
        """
        Updates the title if necessary.
        :return: Always returns WorkerResult.SUCCESS.
        :rtype: WorkerResult
        """
        if not self._should_display():
            return WorkerResult.SUCCESS
        title = self._get_stats_title(self._get_player_stats())
        # If title is empty, it couldn't be generated.
        if not title:
            return WorkerResult.SUCCESS
        self._update_title(title, _platform)
        return WorkerResult.SUCCESS

    def _should_display(self):
        """
        Returns a value indicating whether the title should be updated.
        :return: True if the title should be updated; otherwise, False.
        :rtype: bool
        """
        return self.next_update is None or datetime.now() >= self.next_update

    def _update_title(self, title, platform):
        """
        Updates the window title using different methods, according to the given platform
        :param title: The new window title.
        :type title: string
        :param platform: The platform string.
        :type platform: string
        :return: Nothing.
        :rtype: None
        :raise: RuntimeError: When the given platform isn't supported.
        """
        if platform == "linux" or platform == "linux2"\
                or platform == "cygwin":
            stdout.write("\x1b]2;{}\x07".format(title))
        elif platform == "darwin":
            stdout.write("\033]0;{}\007".format(title))
        elif platform == "win32":
            ctypes.windll.kernel32.SetConsoleTitleA(title)
        else:
            raise RuntimeError("unsupported platform '{}'".format(platform))

        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)

    def _process_config(self):
        """
        Fetches the configuration for this worker and stores the values internally.
        :return: Nothing.
        :rtype: None
        """
        self.min_interval = int(self.config.get('min_interval', self.DEFAULT_MIN_INTERVAL))
        self.displayed_stats = self.config.get('stats', self.DEFAULT_DISPLAYED_STATS)

    def _get_stats_title(self, player_stats):
        """
        Generates a stats string with the given player stats according to the configuration.
        :return: A string containing human-readable stats, ready to be displayed.
        :rtype: string
        """
        # No player stats available, won't be able to gather all informations.
        if player_stats is None:
            return ''
        # No stats to display, avoid any useless overhead.
        if not self.displayed_stats:
            return ''

        # Gather stats values.
        metrics = self.bot.metrics
        metrics.capture_stats()
        runtime = metrics.runtime()
        distance_travelled = metrics.distance_travelled()
        current_level = int(player_stats.get('level', 0))
        prev_level_xp = int(player_stats.get('prev_level_xp', 0))
        next_level_xp = int(player_stats.get('next_level_xp', 0))
        experience = int(player_stats.get('experience', 0))
        current_level_xp = experience - prev_level_xp
        whole_level_xp = next_level_xp - prev_level_xp
        level_completion_percentage = int((current_level_xp * 100) / whole_level_xp)
        experience_per_hour = int(metrics.xp_per_hour())
        xp_earned = metrics.xp_earned()
        stops_visited = metrics.visits['latest'] - metrics.visits['start']
        pokemon_encountered = metrics.num_encounters()
        pokemon_caught = metrics.num_captures()
        pokemon_released = metrics.releases
        pokemon_evolved = metrics.num_evolutions()
        pokemon_unseen = metrics.num_new_mons()
        pokeballs_thrown = metrics.num_throws()
        stardust_earned = metrics.earned_dust()
        highest_cp_pokemon = metrics.highest_cp['desc']
        if not highest_cp_pokemon:
            highest_cp_pokemon = "None"
        most_perfect_pokemon = metrics.most_perfect['desc']
        if not most_perfect_pokemon:
            most_perfect_pokemon = "None"

        # Create stats strings.
        available_stats = {
            'uptime': 'Uptime : {}'.format(runtime),
            'km_walked': '{:,.2f}km walked'.format(distance_travelled),
            'level': 'Level {}'.format(current_level),
            'level_completion': '{:,} / {:,} XP ({}%)'.format(current_level_xp, whole_level_xp,
                                                              level_completion_percentage),
            'level_stats': 'Level {} ({:,} / {:,}, {}%)'.format(current_level, current_level_xp,
                                                                whole_level_xp,
                                                                level_completion_percentage),
            'xp_per_hour': '{:,} XP/h'.format(experience_per_hour),
            'xp_earned': '+{:,} XP'.format(xp_earned),
            'stops_visited': 'Visited {:,} stops'.format(stops_visited),
            'pokemon_encountered': 'Encountered {:,} pokemon'.format(pokemon_encountered),
            'pokemon_caught': 'Caught {:,} pokemon'.format(pokemon_caught),
            'pokemon_released': 'Released {:,} pokemon'.format(pokemon_released),
            'pokemon_evolved': 'Evolved {:,} pokemon'.format(pokemon_evolved),
            'pokemon_unseen': 'Encountered {} new pokemon'.format(pokemon_unseen),
            'pokemon_stats': 'Encountered {:,} pokemon, {:,} caught, {:,} released, {:,} evolved, '
                             '{} never seen before'.format(pokemon_encountered, pokemon_caught,
                                                           pokemon_released, pokemon_evolved,
                                                           pokemon_unseen),
            'pokeballs_thrown': 'Threw {:,} pokeballs'.format(pokeballs_thrown),
            'stardust_earned': 'Earned {:,} Stardust'.format(stardust_earned),
            'highest_cp_pokemon': 'Highest CP pokemon : {}'.format(highest_cp_pokemon),
            'most_perfect_pokemon': 'Most perfect pokemon : {}'.format(most_perfect_pokemon),
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
        title = ' | '.join(map(get_stat, self.displayed_stats))

        return title

    def _get_player_stats(self):
        """
        Helper method parsing the bot inventory object and returning the player stats object.
        :return: The player stats object.
        :rtype: dict
        """
        inventory_items = self.bot.get_inventory() \
            .get('responses', {}) \
            .get('GET_INVENTORY', {}) \
            .get('inventory_delta', {}) \
            .get('inventory_items', {})
        return next((x["inventory_item_data"]["player_stats"]
                     for x in inventory_items
                     if x.get("inventory_item_data", {}).get("player_stats", {})),
                    None)
