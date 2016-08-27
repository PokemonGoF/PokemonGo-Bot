from datetime import datetime, timedelta

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.base_task import BaseTask


class IncubateEggs(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    last_km_walked = 0

    def initialize(self):
        self.next_update = None
        self.ready_incubators = []
        self.used_incubators = []
        self.eggs = []
        self.km_walked = 0
        self.hatching_animation_delay = 4.20
        self.max_iv = 45.0

        self._process_config()

    def _process_config(self):
        self.longer_eggs_first = self.config.get("longer_eggs_first", True)
        self.min_interval = self.config.get('min_interval', 120)
        
        self.breakable_incubator = self.config.get("breakable", [2,5,10])
        self.infinite_incubator = self.config.get("infinite", [2,5,10])
    
    def work(self):
        try:
            self._check_inventory()
        except:
            return

        if self.used_incubators and IncubateEggs.last_km_walked != self.km_walked:
            self.used_incubators.sort(key=lambda x: x.get("km"))
            km_left = self.used_incubators[0]['km']-self.km_walked
            if km_left <= 0:
                self._hatch_eggs()
            else:
                self.bot.metrics.next_hatching_km(km_left)

        if self._should_print():
            self._print_eggs()
            self._compute_next_update()

        IncubateEggs.last_km_walked = self.km_walked

        sorting = self.longer_eggs_first
        self.eggs.sort(key=lambda x: x.get("km"), reverse=sorting)

        if self.ready_incubators:
            self._apply_incubators()

    def _apply_incubators(self):
        for incubator in self.ready_incubators:
            if incubator.get('used', False):
                continue
            for egg in self.eggs:
                if egg["used"] or egg["km"] == -1:
                    continue
                
                # test if the incubator is of type breakable
                if incubator.get('uses_remaining') is not None:
                    if egg["km"] not in self.breakable_incubator:
                        continue
                    
                # test if the incubator is of type infinite
                if incubator.get('uses_remaining') is None:
                    if egg["km"] not in self.infinite_incubator:
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
        inv = {}
        response_dict = self.bot.api.get_inventory()
        matched_pokemon = []
        temp_eggs = []
        temp_used_incubators = []
        temp_ready_incubators = []
        inv = reduce(
            dict.__getitem__,
            ["responses", "GET_INVENTORY", "inventory_delta", "inventory_items"],
            response_dict
        )
        for inv_data in inv:
            inv_data = inv_data.get("inventory_item_data", {})
            if "egg_incubators" in inv_data:
                temp_used_incubators = []
                temp_ready_incubators = []
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
                        temp_ready_incubators.append({
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
                    pokemon.update({
                        "iv": [
                            pokemon.get('individual_attack', 0),
                            pokemon.get('individual_defense', 0),
                            pokemon.get('individual_stamina', 0)
                        ]})
                    matched_pokemon.append(pokemon)
                continue
            if "player_stats" in inv_data:
                self.km_walked = inv_data.get("player_stats", {}).get("km_walked", 0)
        if temp_used_incubators:
            self.used_incubators = temp_used_incubators
        if temp_ready_incubators:
            self.ready_incubators = temp_ready_incubators
        if temp_eggs:
            self.eggs = temp_eggs
        return matched_pokemon

    def _hatch_eggs(self):
        response_dict = self.bot.api.get_hatched_eggs()
        log_color = 'green'
        try:
            result = reduce(dict.__getitem__, ["responses", "GET_HATCHED_EGGS"], response_dict)
        except KeyError:
            return
        pokemon_ids = []
        if 'pokemon_id' in result:
            pokemon_ids = [id for id in result['pokemon_id']]
        stardust = result.get('stardust_awarded', "error")
        candy = result.get('candy_awarded', "error")
        xp = result.get('experience_awarded', "error")
        sleep(self.hatching_animation_delay)
        self.bot.latest_inventory = None
        try:
            pokemon_data = self._check_inventory(pokemon_ids)
            for pokemon in pokemon_data:
                # pokemon ids seem to be offset by one
                if pokemon['pokemon_id']!=-1:
                    pokemon['name'] = self.bot.pokemon_list[(pokemon.get('pokemon_id')-1)]['Name']
                else:
                    pokemon['name'] = "error"
        except:
            pokemon_data = [{"name":"error","cp":"error","iv":"error"}]
        if not pokemon_ids or pokemon_data[0]['name'] == "error":
            self.emit_event(
                'egg_hatched',
                data={
                    'pokemon': 'error',
                    'cp': 'error',
                    'iv': 'error',
                    'exp': 'error',
                    'stardust': 'error',
                    'candy': 'error',
                }
            )
            return
        for i in range(len(pokemon_data)):
            msg = "Egg hatched with a {pokemon} (CP {cp} - IV {iv}), {exp} exp, {stardust} stardust and {candy} candies."
            self.bot.metrics.hatched_eggs(1)
            self.emit_event(
                'egg_hatched',
                formatted=msg,
                data={
                    'pokemon': pokemon_data[i]['name'],
                    'cp': pokemon_data[i]['cp'],
                    'iv': "{} {}".format(
                        "/".join(map(str, pokemon_data[i]['iv'])),
                        round(sum(pokemon_data[i]['iv'])/self.max_iv, 2)
                    ),
                    'exp': xp[i],
                    'stardust': stardust[i],
                    'candy': candy[i],
                }
            )

    def _print_eggs(self):
        if not self.used_incubators:
            return

        self.used_incubators.sort(key=lambda x: x.get("km"))
        
        eggs = ['{:.2f}/{} km'.format(e['km_needed']-e['km']+self.km_walked, e['km_needed']) for e in self.used_incubators]

        self.emit_event(
                    'next_egg_incubates',
                    formatted='Eggs incubating: [{eggs}] (Eggs left: {eggs_left}, Incubating: {eggs_inc})',
                    data={
                        'eggs_left': len(self.eggs),
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
