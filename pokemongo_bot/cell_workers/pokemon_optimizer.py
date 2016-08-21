import copy
import json
import math
import os

from pokemongo_bot import inventory
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.datastore import Datastore
from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot.item_list import Item
from pokemongo_bot.worker_result import WorkerResult

SUCCESS = 1
ERROR_INVALID_ITEM_TYPE = 2
ERROR_XP_BOOST_ALREADY_ACTIVE = 3
ERROR_NO_ITEMS_REMAINING = 4
ERROR_LOCATION_UNSET = 5


class PokemonOptimizer(Datastore, BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(PokemonOptimizer, self).__init__(bot, config)

    def initialize(self):
        self.family_by_family_id = {}
        self.max_pokemon_storage = inventory.get_pokemon_inventory_size()
        self.last_pokemon_count = 0

        self.config_transfer = self.config.get("transfer", False)
        self.config_evolve = self.config.get("evolve", False)
        self.config_evolve_time = self.config.get("evolve_time", 20)
        self.config_evolve_for_xp = self.config.get("evolve_for_xp", True)
        self.config_evolve_only_with_lucky_egg = self.config.get("evolve_only_with_lucky_egg", False)
        self.config_evolve_count_for_lucky_egg = self.config.get("evolve_count_for_lucky_egg", 92)
        self.config_may_use_lucky_egg = self.config.get("may_use_lucky_egg", False)
        self.config_keep = self.config.get("keep", [{"top": 1, "evolve": True, "sort": ["iv"]},
                                                    {"top": 1, "evolve": True, "sort": ["ncp"]},
                                                    {"top": 1, "evolve": False, "sort": ["cp"]}])

        self.config_transfer_wait_min = self.config.get("transfer_wait_min", 1)
        self.config_transfer_wait_max = self.config.get("transfer_wait_max", 4)

        if (not self.config_may_use_lucky_egg) and self.config_evolve_only_with_lucky_egg:
            self.config_evolve = False

    def get_pokemon_slot_left(self):
        pokemon_count = inventory.Pokemons.get_space_used()

        if pokemon_count != self.last_pokemon_count:
            self.last_pokemon_count = pokemon_count
            self.logger.info("Pokemon Bag: %s/%s", pokemon_count, self.max_pokemon_storage)
            self.save_web_inventory()

        return inventory.Pokemons.get_space_left()

    def work(self):
        if (not self.enabled) or (self.get_pokemon_slot_left() > 5):
            return WorkerResult.SUCCESS

        self.open_inventory()

        transfer_all = []
        evo_all_best = []
        evo_all_crap = []

        for family_id, family in self.family_by_family_id.items():
            if family_id == 133:  # "Eevee"
                transfer, evo_best, evo_crap = self.get_multi_family_optimized(family_id, family, 3)
            else:
                transfer, evo_best, evo_crap = self.get_family_optimized(family_id, family)

            transfer_all += transfer
            evo_all_best += evo_best
            evo_all_crap += evo_crap

        evo_all = evo_all_best + evo_all_crap

        self.apply_optimization(transfer_all, evo_all)
        self.save_web_inventory()

        return WorkerResult.SUCCESS

    def open_inventory(self):
        self.family_by_family_id.clear()

        for pokemon in inventory.pokemons().all():
            family_id = pokemon.first_evolution_id
            setattr(pokemon, "ncp", pokemon.cp_percent)
            setattr(pokemon, "dps", pokemon.moveset.dps)
            setattr(pokemon, "dps_attack", pokemon.moveset.dps_attack)
            setattr(pokemon, "dps_defense", pokemon.moveset.dps_defense)

            self.family_by_family_id.setdefault(family_id, []).append(pokemon)

    def save_web_inventory(self):
        web_inventory = os.path.join(_base_dir, "web", "inventory-%s.json" % self.bot.config.username)

        with open(web_inventory, "r") as infile:
            ii = json.load(infile)

        ii = [x for x in ii if not x.get("inventory_item_data", {}).get("pokedex_entry", None)]
        ii = [x for x in ii if not x.get("inventory_item_data", {}).get("candy", None)]
        ii = [x for x in ii if not x.get("inventory_item_data", {}).get("item", None)]
        ii = [x for x in ii if not x.get("inventory_item_data", {}).get("pokemon_data", None)]

        for pokedex in inventory.pokedex().all():
            ii.append({"inventory_item_data": {"pokedex_entry": pokedex}})

        for family_id, candy in inventory.candies()._data.items():
            ii.append({"inventory_item_data": {"candy": {"family_id": family_id, "candy": candy.quantity}}})

        for item_id, item in inventory.items()._data.items():
            ii.append({"inventory_item_data": {"item": {"item_id": item_id, "count": item.count}}})

        for pokemon in inventory.pokemons().all():
            ii.append({"inventory_item_data": {"pokemon_data": pokemon._data}})

        with open(web_inventory, "w") as outfile:
            json.dump(ii, outfile)

    def get_family_optimized(self, family_id, family):
        evolve_best = []
        keep_best = []
        family_names = self.get_family_names(family_id)

        for criteria in self.config_keep:
            names = criteria.get("names", [])

            if names and not any(n in family_names for n in names):
                continue

            if criteria.get("evolve", True):
                evolve_best += self.get_top_rank(family, criteria)
            else:
                keep_best += self.get_top_rank(family, criteria)

        evolve_best = self.unique_pokemon(evolve_best)
        keep_best = self.unique_pokemon(keep_best)

        return self.get_evolution_plan(family_id, family, evolve_best, keep_best)

    def get_multi_family_optimized(self, family_id, family, nb_branch):
        # Transfer each group of senior independently
        senior_family = [p for p in family if not p.has_next_evolution()]
        other_family = [p for p in family if p.has_next_evolution()]
        senior_pids = set(p.pokemon_id for p in senior_family)
        senior_grouped_family = {pid: [p for p in senior_family if p.pokemon_id == pid] for pid in senior_pids}

        if not self.config_evolve:
            transfer, evo_best, evo_crap = self.get_family_optimized(family_id, other_family)
        elif len(senior_pids) < nb_branch:
            # We did not get every combination yet = All other Pokemon are potentially good to keep
            transfer, evo_best, evo_crap = self.get_evolution_plan(family_id, [], other_family, [])
            evo_best.sort(key=lambda p: p.iv * p.ncp, reverse=True)
        else:
            evolve_best = []
            keep_best = []
            names = self.get_family_names(family_id)

            for criteria in self.config_keep:
                family_names = criteria.get("names", [])

                if names and not any(n in family_names for n in names):
                    continue

                top = []

                for f in senior_grouped_family.values():
                    top += self.get_top_rank(f, criteria)

                worst = self.get_sorted_family(top, criteria)[-1]

                if criteria.get("evolve", True):
                    evolve_best += self.get_better_rank(family, criteria, worst)
                else:
                    keep_best += self.get_better_rank(family, criteria, worst)

            evolve_best = self.unique_pokemon(evolve_best)
            keep_best = self.unique_pokemon(keep_best)
            transfer, evo_best, evo_crap = self.get_evolution_plan(family_id, other_family, evolve_best, keep_best)

        for senior_pid, senior_family in senior_grouped_family.items():
            transfer += self.get_family_optimized(senior_pid, senior_family)[0]

        return (transfer, evo_best, evo_crap)

    def get_family_names(self, family_id):
        ids = [family_id]
        ids += inventory.Pokemons.data_for(family_id).next_evolutions_all[:]
        datas = [inventory.Pokemons.data_for(x) for x in ids]
        return [x.name for x in datas]

    def get_top_rank(self, family, criteria):
        sorted_family = self.get_sorted_family(family, criteria)
        index = criteria.get("top", 1) - 1

        if 0 <= index < len(sorted_family):
            worst = sorted_family[index]
            return [p for p in sorted_family if self.get_rank(p, criteria) >= self.get_rank(worst, criteria)]
        else:
            return sorted_family

    def get_better_rank(self, family, criteria, worst):
        return [p for p in self.get_sorted_family(family, criteria) if self.get_rank(p, criteria) >= self.get_rank(worst, criteria)]

    def get_sorted_family(self, family, criteria):
        return sorted(family, key=lambda p: self.get_rank(p, criteria), reverse=True)

    def get_rank(self, pokemon, criteria):
        return tuple(getattr(pokemon, a, None) for a in criteria.get("sort"))

    def get_pokemon_max_cp(self, pokemon_name):
        return int(self.pokemon_max_cp.get(pokemon_name, 0))

    def unique_pokemon(self, l):
        seen = set()
        return [p for p in l if not (p.unique_id in seen or seen.add(p.unique_id))]

    def get_evolution_plan(self, family_id, family, evolve_best, keep_best):
        candies = inventory.candies().get(family_id).quantity

        # All the rest is crap, for now
        crap = family[:]
        crap = [p for p in crap if p not in evolve_best]
        crap = [p for p in crap if p not in keep_best]
        crap = [p for p in crap if not p.in_fort and not p.is_favorite]
        crap.sort(key=lambda p: p.iv * p.ncp, reverse=True)

        # We will gain a candy whether we choose to transfer or evolve these Pokemon
        candies += len(crap)

        # Let's see if we can evolve our best Pokemon
        can_evolve_best = []

        for pokemon in evolve_best:
            if not pokemon.has_next_evolution():
                continue

            candies -= pokemon.evolution_cost

            if candies < 0:
                break

            candies += 1
            can_evolve_best.append(pokemon)

            # Not sure if the evo keep the same id
            next_pid = pokemon.next_evolution_ids[0]
            next_evo = copy.copy(pokemon)
            next_evo.pokemon_id = next_pid
            next_evo.static = inventory.pokemons().data_for(next_pid)
            next_evo.name = inventory.pokemons().name_for(next_pid)
            evolve_best.append(next_evo)

        if self.config_evolve_for_xp:
            # Compute how many crap we should keep if we want to batch evolve them for xp
            junior_evolution_cost = inventory.pokemons().evolution_cost_for(family_id)

            # transfer + keep_for_evo = len(crap)
            # leftover_candies = candies - len(crap) + transfer * 1
            # keep_for_evo = (leftover_candies - 1) / (junior_evolution_cost - 1)
            # keep_for_evo = (candies - len(crap) + transfer - 1) / (junior_evolution_cost - 1)
            # keep_for_evo = (candies - keep_for_evo - 1) / (junior_evolution_cost - 1)

            if (candies > 0) and junior_evolution_cost:
                keep_for_evo = int((candies - 1) / junior_evolution_cost)
            else:
                keep_for_evo = 0

            evo_crap = [p for p in crap if p.has_next_evolution() and p.evolution_cost == junior_evolution_cost][:keep_for_evo]

            # If not much to evolve, better keep the candies
            if len(evo_crap) < math.ceil(self.max_pokemon_storage * 0.01):
                evo_crap = []

            transfer = [p for p in crap if p not in evo_crap]
        else:
            evo_crap = []
            transfer = crap

        return (transfer, can_evolve_best, evo_crap)

    def apply_optimization(self, transfer, evo):
        self.logger.info("Transferring %s Pokemon", len(transfer))

        for pokemon in transfer:
            self.transfer_pokemon(pokemon)

        if len(evo) == 0:
            return

        if self.config_evolve and self.config_may_use_lucky_egg and (not self.bot.config.test):
            lucky_egg = inventory.items().get(Item.ITEM_LUCKY_EGG.value)  # @UndefinedVariable

            if lucky_egg.count == 0:
                if self.config_evolve_only_with_lucky_egg:
                    self.emit_event("skip_evolve",
                                    formatted="Skipping evolution step. No lucky egg available")
                    return
            elif len(evo) < self.config_evolve_count_for_lucky_egg:
                if self.config_evolve_only_with_lucky_egg:
                    self.emit_event("skip_evolve",
                                    formatted="Skipping evolution step. Not enough Pokemon to evolve with lucky egg: %s/%s" % (len(evo), self.config_evolve_count_for_lucky_egg))
                    return
                elif self.get_pokemon_slot_left() > 5:
                    self.emit_event("skip_evolve",
                                    formatted="Waiting for more Pokemon to evolve with lucky egg: %s/%s" % (len(evo), self.config_evolve_count_for_lucky_egg))
                    return
            else:
                self.use_lucky_egg()

        self.logger.info("Evolving %s Pokemon", len(evo))

        for pokemon in evo:
            self.evolve_pokemon(pokemon)

    def transfer_pokemon(self, pokemon):
        if self.config_transfer and (not self.bot.config.test):
            response_dict = self.bot.api.release_pokemon(pokemon_id=pokemon.unique_id)
        else:
            response_dict = {"responses": {"RELEASE_POKEMON": {"candy_awarded": 0}}}

        if not response_dict:
            return False

        candy_awarded = response_dict.get("responses", {}).get("RELEASE_POKEMON", {}).get("candy_awarded", 0)
        candy = inventory.candies().get(pokemon.pokemon_id)

        if self.config_transfer and (not self.bot.config.test):
            candy.add(candy_awarded)

        self.emit_event("pokemon_release",
                        formatted="Exchanged {pokemon} [IV {iv}] [CP {cp}] [{candy} candies]",
                        data={"pokemon": pokemon.name,
                              "iv": pokemon.iv,
                              "cp": pokemon.cp,
                              "candy": candy.quantity})

        if self.config_transfer and (not self.bot.config.test):
            inventory.pokemons().remove(pokemon.unique_id)

            with self.bot.database as db:
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='transfer_log'")

                db_result = cursor.fetchone()

                if db_result[0] == 1:
                    db.execute("INSERT INTO transfer_log (pokemon, iv, cp) VALUES (?, ?, ?)", (pokemon.name, pokemon.iv, pokemon.cp))

            action_delay(self.config_transfer_wait_min, self.config_transfer_wait_max)

        return True

    def use_lucky_egg(self):
        lucky_egg = inventory.items().get(Item.ITEM_LUCKY_EGG.value)  # @UndefinedVariable

        if lucky_egg.count == 0:
            return False

        response_dict = self.bot.use_lucky_egg()

        if not response_dict:
            self.emit_event("lucky_egg_error",
                            level='error',
                            formatted="Failed to use lucky egg!")
            return False

        result = response_dict.get("responses", {}).get("USE_ITEM_XP_BOOST", {}).get("result", 0)

        if result == SUCCESS:
            lucky_egg.remove(1)

            self.emit_event("used_lucky_egg",
                            formatted="Used lucky egg ({amount_left} left).",
                            data={"amount_left": lucky_egg.count})
            return True
        elif result == ERROR_XP_BOOST_ALREADY_ACTIVE:
            self.emit_event("used_lucky_egg",
                            formatted="Lucky egg already active ({amount_left} left).",
                            data={"amount_left": lucky_egg.count})
            return True
        else:
            self.emit_event("lucky_egg_error",
                            level='error',
                            formatted="Failed to use lucky egg!")
            return False

    def evolve_pokemon(self, pokemon):
        if self.config_evolve and (not self.bot.config.test):
            response_dict = self.bot.api.evolve_pokemon(pokemon_id=pokemon.unique_id)
        else:
            response_dict = {"responses": {"EVOLVE_POKEMON": {"result": 1}}}

        if not response_dict:
            return False

        result = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("result", 0)

        if result != SUCCESS:
            return False

        xp = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("experience_awarded", 0)
        candy_awarded = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("candy_awarded", 0)
        candy = inventory.candies().get(pokemon.pokemon_id)
        evolution = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("evolved_pokemon_data", {})

        if self.config_evolve and (not self.bot.config.test):
            candy.consume(pokemon.evolution_cost - candy_awarded)

        self.emit_event("pokemon_evolved",
                        formatted="Evolved {pokemon} [IV {iv}] [CP {cp}] [{candy} candies] [+{xp} xp]",
                        data={"pokemon": pokemon.name,
                              "iv": pokemon.iv,
                              "cp": pokemon.cp,
                              "candy": candy.quantity,
                              "xp": xp})

        if self.config_evolve and (not self.bot.config.test):
            inventory.pokemons().remove(pokemon.unique_id)

            new_pokemon = inventory.Pokemon(evolution)
            inventory.pokemons().add(new_pokemon)

            with self.bot.database as db:
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table' AND name='evolve_log'")

                db_result = cursor.fetchone()

                if db_result[0] == 1:
                    db.execute("INSERT INTO evolve_log (pokemon, iv, cp) VALUES (?, ?, ?)", (pokemon.name, pokemon.iv, pokemon.cp))

            sleep(self.config_evolve_time)

        return True
