from collections import Counter
from datetime import datetime, timedelta

from pokemongo_bot import inventory
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.worker_result import WorkerResult
from functools import reduce


class IncubateEggs(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    last_km_walked = 0

    def __init__(self, bot, config):
        super(IncubateEggs, self).__init__(bot, config)

    def initialize(self):
        self.next_update = None
        self.ready_breakable_incubators = []
        self.ready_infinite_incubators = []
        self.used_incubators = []
        self.eggs = []
        self.km_walked = 0
        self.hatching_animation_delay = 4.20

        self._process_config()

    def _process_config(self):
        self.infinite_longer_eggs_first = self.config.get("infinite_longer_eggs_first", False)
        self.breakable_longer_eggs_first = self.config.get("breakable_longer_eggs_first", True)
        self.min_interval = self.config.get('min_interval', 120)
        self.breakable_incubator = self.config.get("breakable", [2,5,10])
        self.infinite_incubator = self.config.get("infinite", [2,5,10])

    def work(self):
        try:
            self._check_inventory()
        except:
            return WorkerResult.ERROR

        if self.used_incubators and IncubateEggs.last_km_walked != self.km_walked:
            km_left = self.used_incubators[0]['km']-self.km_walked
            if km_left <= 0:
                if not self._hatch_eggs():
                    return WorkerResult.ERROR
            else:
                self.bot.metrics.next_hatching_km(km_left)

        if self._should_print():
            self._print_eggs()
            self._compute_next_update()

        IncubateEggs.last_km_walked = self.km_walked

        # if there is a ready infinite incubator
        if self.ready_infinite_incubators:
            # get available eggs
            eggs = self._filter_sort_eggs(self.infinite_incubator,
                    self.infinite_longer_eggs_first)
            self._apply_incubators(eggs, self.ready_infinite_incubators)
        if self.ready_breakable_incubators:
            # get available eggs
            eggs = self._filter_sort_eggs(self.breakable_incubator,
                    self.breakable_longer_eggs_first)
            self._apply_incubators(eggs, self.ready_breakable_incubators)

        return WorkerResult.SUCCESS


    def _filter_sort_eggs(self, allowed, sorting):
        eligible_eggs = filter(lambda egg: int(egg["km"]) in allowed, self.eggs)
        eligible_eggs.sort(key=lambda egg: egg["km"], reverse=sorting)

        return eligible_eggs


    def _apply_incubators(self, available_eggs, available_incubators):
        for incubator in available_incubators:
            for egg in available_eggs:
                if egg["used"] or egg["km"] == -1:
                    continue

                self.emit_event(
                    'incubate_try',
                    level='debug',
                    formatted="Attempting to apply incubator {incubator_id} to egg {egg_id}",
                    data={
                        'incubator_id': incubator['id'],
                        'egg_id': egg['id']
                    }
                )
                ret = self.bot.api.use_item_egg_incubator(
                    item_id=incubator["id"],
                    pokemon_id=egg["id"]
                )
                if ret:
                    code = ret.get("responses", {}).get("USE_ITEM_EGG_INCUBATOR", {}).get("result", 0)
                    if code == 1:
                        self.emit_event(
                            'incubate',
                            formatted='Incubating a {distance_in_km} egg.',
                            data={
                                'distance_in_km': str(egg['km'])
                            }
                        )
                        egg["used"] = True
                        incubator["used"] = True
                        break
                    elif code == 5 or code == 7:
                        self.emit_event(
                            'incubator_already_used',
                            level='debug',
                            formatted='Incubator in use.',
                        )
                        incubator["used"] = True
                        break
                    elif code == 6:
                        self.emit_event(
                            'egg_already_incubating',
                            level='debug',
                            formatted='Egg already incubating',
                        )
                        egg["used"] = True

    def _check_inventory(self, lookup_ids=[]):
        if lookup_ids:
            inventory.refresh_inventory()
        matched_pokemon = []
        temp_eggs = []
        temp_used_incubators = []
        temp_ready_breakable_incubators = []
        temp_ready_infinite_incubators = []
        inv = inventory.jsonify_inventory()
        for inv_data in inv:
            inv_data = inv_data.get("inventory_item_data", {})
            if "egg_incubators" in inv_data:
                incubators = inv_data.get("egg_incubators", {}).get("egg_incubator",[])
                if isinstance(incubators, basestring):  # checking for old response
                    incubators = [incubators]
                for incubator in incubators:
                    if 'pokemon_id' in incubator:
                        start_km = incubator.get('start_km_walked', 0)
                        km_walked = incubator.get('target_km_walked', 0)
                        temp_used_incubators.append({
                            "id": incubator.get('id', -1),
                            "km": km_walked,
                            "km_needed": (km_walked - start_km)
                        })
                    else:
                        if incubator.get('uses_remaining') is not None:
                            temp_ready_breakable_incubators.append({
                                "id": incubator.get('id', -1)
                            })
                        else:
                            temp_ready_infinite_incubators.append({
                                "id": incubator.get('id', -1)
                            })
                continue
            if "pokemon_data" in inv_data:
                pokemon = inv_data.get("pokemon_data", {})
                if pokemon.get("is_egg", False) and "egg_incubator_id" not in pokemon:
                    temp_eggs.append({
                        "id": pokemon.get("id", -1),
                        "km": pokemon.get("egg_km_walked_target", -1),
                        "used": False
                    })
                elif 'is_egg' not in pokemon and pokemon['id'] in lookup_ids:
                    matched_pokemon.append(pokemon)
                continue
            if "player_stats" in inv_data:
                self.km_walked = inv_data.get("player_stats", {}).get("km_walked", 0)

        self.used_incubators = temp_used_incubators
        if self.used_incubators:
            self.used_incubators.sort(key=lambda x: x.get("km"))
        self.ready_breakable_incubators = temp_ready_breakable_incubators
        self.ready_infinite_incubators = temp_ready_infinite_incubators
        self.eggs = temp_eggs
        return matched_pokemon

    def _hatch_eggs(self):
        response_dict = self.bot.api.get_hatched_eggs()
        try:
            result = reduce(dict.__getitem__, ["responses", "GET_HATCHED_EGGS"], response_dict)
        except KeyError:
            return WorkerResult.ERROR
        pokemon_ids = []
        if 'pokemon_id' in result:
            pokemon_ids = [id for id in result['pokemon_id']]
        stardust = result.get('stardust_awarded', [])
        candy = result.get('candy_awarded', [])
        xp = result.get('experience_awarded', [])
        sleep(self.hatching_animation_delay)
        try:
            pokemon_data = self._check_inventory(pokemon_ids)
            pokemon_list = [inventory.Pokemon(p) for p in pokemon_data]
            for pokemon in pokemon_list:
                inventory.pokemons().remove(pokemon.unique_id)
                inventory.pokemons().add(pokemon)
        except:
            pokemon_data = []
        if not pokemon_ids or not pokemon_data:
            self.emit_event(
                'egg_hatched_fail',
                formatted= "Error trying to hatch egg."
            )
            return False

        for i in range(len(pokemon_list)):
            pokemon = pokemon_list[i]
            msg = "Egg hatched with a {name} (CP {cp} - NCP {ncp} - IV {iv_ads} {iv_pct}), {exp} exp, {stardust} stardust and {candy} candies."
            self.emit_event(
                'egg_hatched',
                formatted=msg,
                data={
                    'name': pokemon.name,
                    'cp': str(int(pokemon.cp)),
                    'ncp': str(round(pokemon.cp_percent, 2)),
                    'iv_ads': str(pokemon.iv_display),
                    'iv_pct': str(pokemon.iv),
                    'exp': str(xp[i]),
                    'stardust': str(stardust[i]),
                    'candy': str(candy[i])
                }
            )
            # hatching egg gets exp too!
            inventory.player().exp += xp[i]
            self.bot.stardust += stardust[i]

            with self.bot.database as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='eggs_hatched_log'")
            result = c.fetchone()
            while True:
                if result[0] == 1:
                    conn.execute('''INSERT INTO eggs_hatched_log (pokemon, cp, iv, pokemon_id) VALUES (?, ?, ?, ?)''', (pokemon.name, pokemon.cp, pokemon.iv, pokemon.pokemon_id))
                    break
                else:
                    self.emit_event(
                        'eggs_hatched_log',
                        sender=self,
                        level='info',
                        formatted="eggs_hatched_log table not found, skipping log"
                    )
                    break

        self.bot.metrics.hatched_eggs(len(pokemon_list))
        return True

    def _print_eggs(self):
        if not self.used_incubators:
            return

        eggs = ['{:.2f}/{} km'.format(e['km_needed']-e['km']+self.km_walked, e['km_needed']) for e in self.used_incubators]
        all_eggs = Counter([egg['km'] for egg in self.eggs])

        self.emit_event(
            'next_egg_incubates',
            formatted='Eggs incubating: {eggs} (Eggs left: {eggs_left}, Incubating: {eggs_inc})',
            data={
                'eggs_left': str(sorted(all_eggs.iteritems())).strip('[]'),
                'eggs_inc': len(self.used_incubators),
                'eggs': ', '.join(eggs)
            }
        )

    def _should_print(self):
        """
        Returns a value indicating whether the eggs should be displayed.
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
