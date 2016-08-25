import ctypes
from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from pokemongo_bot.tree_config_builder import ConfigException


class ShowBestPokemon(BaseTask):
    """
    Periodically displays the user inventory in the terminal.

    Example config :
    {
        "type": "UpdateLiveInventory",
        "config": {
          "enabled": true,
          "min_interval": 120,
          "show_all_multiple_lines": false,
          "items": ["space_info", "pokeballs", "greatballs", "ultraballs", "razzberries", "luckyegg"]
        }
    }

    min_interval : The minimum interval at which the stats are displayed,
                   in seconds (defaults to 120 seconds).
                   The update interval cannot be accurate as workers run synchronously.
    show_all_multiple_lines : Logs all items on inventory using multiple lines.
                              Ignores configuration of 'items' 
    items : An array of items to display and their display order (implicitly),
            see available items below (defaults to []).

    Available items :
		'pokemon_bag' : pokemon in inventory (i.e. 'Pokemon Bag: 100/250')
        'space_info': not an item but shows inventory bag space (i.e. 'Items: 140/350')
        'pokeballs'
        'greatballs'
        'ultraballs'
        'masterballs'
        'razzberries'
        'blukberries'
        'nanabberries'
        'luckyegg'
        'incubator'
        'troydisk'
        'potion'
        'superpotion'
        'hyperpotion'
        'maxpotion'
        'incense'
        'incensespicy'
        'incensecool'
        'revive'
        'maxrevive'
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
        Displays the items if necessary.
        :return: Always returns WorkerResult.SUCCESS.
        :rtype: WorkerResult
        """
        if not self.info_to_show or not self._should_print():
            return WorkerResult.SUCCESS

        self.pokemons = inventory.pokemons().all()

        line = self._get_pokemons_line()
        if not line:
            return WorkerResult.SUCCESS

        self.print_pokemons(line)
        return WorkerResult.SUCCESS

    def _should_print(self):
        """
        Returns a value indicating whether the items should be displayed.
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
        Logs the items into the terminal using an event.
        :param items: The items to display.
        :type items: string
        :param is_debug: If True emits event at debug level.
        :type is_debug: boolean
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
