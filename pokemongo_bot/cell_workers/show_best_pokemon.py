import ctypes
from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.tree_config_builder import ConfigException


class ShowBestPokemon(BaseTask):
    """
    Periodically displays the user best pokemon in the terminal.

    Example config :
    {
        "type": "ShowBestPokemon",
        "config": {
          "enabled": true,
          "min_interval": 60,
          "amount": 5,
          "order_by": "cp",
          "info_to_show": ["cp", "ivcp", "dps"]
        }
    }

    min_interval : The minimum interval at which the pokemon are displayed,
                   in seconds (defaults to 120 seconds).
                   The update interval cannot be accurate as workers run synchronously.
    amount : Amount of pokemon to show
    order_by : Stat that will be used to get best pokemons
               Available Stats: 'cp', 'iv', 'ivcp', 'ncp', 'dps', 'hp', 'level'
    info_to_show : Info to show for each pokemon

    Available info_to_show :
        'cp',
        'iv_ads',
        'iv_pct',
        'ivcp',
        'ncp',
        'level',
        'hp',
        'moveset',
        'dps'
    """

    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.next_update = None
        self.min_interval = self.config.get('min_interval', 120)
        self.amount = self.config.get('amount', 3)
        self.order_by = self.config.get('order_by', 'cp')
        self.info_to_show = self.config.get('info_to_show', [])

    def work(self):
        """
        Displays the pokemon if necessary.
        :return: Always returns WorkerResult.SUCCESS.
        :rtype: WorkerResult
        """
        if not self.info_to_show or not self.amount or not self._should_print():
            return WorkerResult.SUCCESS

        self.pokemons = inventory.pokemons().all()

        line = self._get_pokemons_line()
        if not line:
            return WorkerResult.SUCCESS

        self.print_pokemons(line)
        return WorkerResult.SUCCESS

    def _should_print(self):
        """
        Returns a value indicating whether the pokemon should be displayed.
        :return: True if the stats should be displayed; otherwise, False.
        :rtype: bool
        """
        return self.next_update is None or datetime.now() >= self.next_update

    def _compute_next_update(self):
        """
        Computes the next update datetime based on the minimum update interval.
        :return: Nothing.
        :rtype: None
        """
        self.next_update = datetime.now() + timedelta(seconds=self.min_interval)

    def print_pokemons(self, pokemons):
        """
        Logs the pokemon into the terminal using an event.
        :param pokemons: The pokemon to display.
        :type pokemons: string
        :return: Nothing.
        :rtype: None
        """
        self.emit_event(
            'show_best_pokemon',
            formatted="{pokemons}",
            data={
                'pokemons': pokemons
            }
        )

        self._compute_next_update()

    def _get_pokemons_line(self):
        """
        Generates a string according to the configuration.
        :return: A string containing pokemons and their info, ready to be displayed.
        :rtype: string
        """
        def get_poke_info(info, pokemon):
            poke_info = {
                'cp': pokemon.cp,
                'iv': pokemon.iv,
                'ivcp': pokemon.ivcp,
                'ncp': pokemon.cp_percent,
                'level': pokemon.level,
                'hp': pokemon.hp,
                'dps': pokemon.moveset.dps
            }
            if info not in poke_info:
                raise ConfigException("order by {}' isn't available".format(self.order_by))
            return poke_info[info]

        def get_poke_info_formatted(info, pokemon):
            poke_info = {
                'name': pokemon.name,
                'cp': 'CP {}'.format(pokemon.cp),
                'iv_ads': 'A/D/S {}/{}/{}'.format(pokemon.iv_attack, pokemon.iv_defense, pokemon.iv_stamina),
                'iv_pct': 'IV {}'.format(pokemon.iv),
                'ivcp': 'IVCP {}'.format(round(pokemon.ivcp,2)),
                'ncp': 'NCP {}'.format(round(pokemon.cp_percent,2)),
                'level': "Level {}".format(pokemon.level),
                'hp': 'HP {}/{}'.format(pokemon.hp, pokemon.hp_max),
                'moveset': 'Moves: {}'.format(pokemon.moveset),
                'dps': 'DPS {}'.format(round(pokemon.moveset.dps, 2))
            }
            if info not in poke_info:
                raise ConfigException("info '{}' isn't available for displaying".format(info))
            return poke_info[info]

        info_to_show = ['name'] + self.info_to_show

        pokemons_ordered = sorted(self.pokemons, key=lambda x: get_poke_info(self.order_by, x), reverse=True)
        pokemons_ordered = pokemons_ordered[:self.amount]

        poke_info = ['[{}]'.format(', '.join([get_poke_info_formatted(x, p) for x in info_to_show])) for p in pokemons_ordered]

        line = ' | '.join(poke_info)
        return line
