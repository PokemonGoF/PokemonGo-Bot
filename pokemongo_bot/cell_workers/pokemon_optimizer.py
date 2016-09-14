import difflib
import itertools
import json
import math
import os

from pokemongo_bot import inventory
from pokemongo_bot.base_dir import _base_dir
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot.item_list import Item
from pokemongo_bot.tree_config_builder import ConfigException
from pokemongo_bot.worker_result import WorkerResult

SUCCESS = 1
ERROR_INVALID_ITEM_TYPE = 2
ERROR_XP_BOOST_ALREADY_ACTIVE = 3
ERROR_NO_ITEMS_REMAINING = 4
ERROR_LOCATION_UNSET = 5


class PokemonOptimizer(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def __init__(self, bot, config):
        super(PokemonOptimizer, self).__init__(bot, config)

    def initialize(self):
        self.max_pokemon_storage = inventory.get_pokemon_inventory_size()
        self.last_pokemon_count = 0
        self.pokemon_names = [p.name for p in inventory.pokemons().STATIC_DATA]
        self.ongoing_stardust_count = 0

        pokemon_upgrade_cost_file = os.path.join(_base_dir, "data", "pokemon_upgrade_cost.json")

        with open(pokemon_upgrade_cost_file, "r") as fd:
            self.pokemon_upgrade_cost = json.load(fd)

        if self.config.get("keep", None) is not None:
            raise ConfigException("Pokemon Optimizer configuration has changed. See docs/pokemon_optimized.md or configs/config.json.optimizer.example")

        self.config_min_slots_left = self.config.get("min_slots_left", 5)
        self.config_transfer = self.config.get("transfer", False)
        self.config_transfer_wait_min = self.config.get("transfer_wait_min", 3)
        self.config_transfer_wait_max = self.config.get("transfer_wait_max", 5)
        self.config_evolve = self.config.get("evolve", False)
        self.config_evolve_time = self.config.get("evolve_time", 25)
        self.config_evolve_for_xp = self.config.get("evolve_for_xp", True)
        self.config_evolve_only_with_lucky_egg = self.config.get("evolve_only_with_lucky_egg", False)
        self.config_evolve_count_for_lucky_egg = self.config.get("evolve_count_for_lucky_egg", 80)
        self.config_may_use_lucky_egg = self.config.get("may_use_lucky_egg", False)
        self.config_upgrade = self.config.get("upgrade", False)
        self.config_upgrade_level = self.config.get("upgrade_level", 60)
        self.config_groups = self.config.get("groups", {"gym": ["Dragonite", "Snorlax", "Lapras", "Arcanine"]})
        self.config_rules = self.config.get("rules", [{"mode": "by_family", "top": 1, "sort": ["iv"], "evolve": {"iv": 0.9}},
                                                      {"mode": "by_family", "top": 1, "sort": ["ncp"], "evolve": {"ncp": 0.9}},
                                                      {"mode": "by_family", "top": 1, "sort": ["cp"]},
                                                      {"mode": "by_family", "top": 3, "names": ["gym"], "sort": ["iv", "ncp"], "evolve": {"iv": 0.9, "ncp": 0.9}, "upgrade": {"iv": 0.9, "ncp": 0.9}}])

        if (not self.config_may_use_lucky_egg) and self.config_evolve_only_with_lucky_egg:
            self.config_evolve = False

    def get_pokemon_slot_left(self):
        pokemon_count = inventory.Pokemons.get_space_used()

        if pokemon_count != self.last_pokemon_count:
            self.last_pokemon_count = pokemon_count
            self.logger.info("Pokemon Bag: %s/%s", pokemon_count, self.max_pokemon_storage)
            inventory.update_web_inventory()

        return inventory.Pokemons.get_space_left()

    def work(self):
        if (not self.enabled) or (self.get_pokemon_slot_left() > self.config_min_slots_left):
            return WorkerResult.SUCCESS

        self.open_inventory()

        keep_all = []
        try_evolve_all = []
        try_upgrade_all = []

        for rule in self.config_rules:
            mode = rule.get("mode", "by_family")
            names = rule.get("names", [])
            whitelist_names, blacklist_names = self.get_colorlist_names(names)

            if mode == "by_pokemon":
                for pokemon_id, pokemon_list in self.group_by_pokemon_id(inventory.pokemons().all()):
                    name = inventory.pokemons().name_for(pokemon_id)

                    if name in blacklist_names:
                        continue

                    if whitelist_names and (name not in whitelist_names):
                        continue

                    keep, try_evolve, try_upgrade = self.get_best_pokemon_for_rule(pokemon_list, rule)
                    keep_all += keep
                    try_evolve_all += try_evolve
                    try_upgrade_all += try_upgrade
            elif mode == "by_family":
                for family_id, pokemon_list in self.group_by_family_id(inventory.pokemons().all()):
                    matching_names = self.get_family_names(family_id)

                    if any(n in blacklist_names for n in matching_names):
                        continue

                    if whitelist_names and not any(n in whitelist_names for n in matching_names):
                        continue

                    if family_id == 133:  # "Eevee"
                        keep, try_evolve, try_upgrade = self.get_multi_best_pokemon_for_rule(pokemon_list, rule, 3)
                    else:
                        keep, try_evolve, try_upgrade = self.get_best_pokemon_for_rule(pokemon_list, rule)

                    keep_all += keep
                    try_evolve_all += try_evolve
                    try_upgrade_all += try_upgrade
            elif mode == "overall":
                pokemon_list = []

                for pokemon in inventory.pokemons().all():
                    name = pokemon.name

                    if name in blacklist_names:
                        continue

                    if whitelist_names and (name not in whitelist_names):
                        continue

                    pokemon_list.append(pokemon)

                keep, try_evolve, try_upgrade = self.get_best_pokemon_for_rule(pokemon_list, rule)
                keep_all += keep
                try_evolve_all += try_evolve
                try_upgrade_all += try_upgrade

        keep_all = self.unique_pokemon_list(keep_all)
        try_evolve_all = self.unique_pokemon_list(try_evolve_all)
        try_upgrade_all = self.unique_pokemon_list(try_upgrade_all)

        transfer_all = []
        evolve_all = []
        upgrade_all = []
        xp_all = []

        for family_id, pokemon_list in self.group_by_family_id(inventory.pokemons().all()):
            keep = [p for p in keep_all if self.get_family_id(p) == family_id]
            try_evolve = [p for p in try_evolve_all if self.get_family_id(p) == family_id]
            try_upgrade = [p for p in try_upgrade_all if self.get_family_id(p) == family_id]

            transfer, evolve, upgrade, xp = self.get_evolution_plan(family_id, pokemon_list, keep, try_evolve, try_upgrade)

            transfer_all += transfer
            evolve_all += evolve
            upgrade_all += upgrade
            xp_all += xp

        self.apply_optimization(transfer_all, evolve_all, upgrade_all, xp_all)

        return WorkerResult.SUCCESS

    def open_inventory(self):
        for pokemon in inventory.pokemons().all():
            setattr(pokemon, "ncp", pokemon.cp_percent)
            setattr(pokemon, "dps", pokemon.moveset.dps)
            setattr(pokemon, "dps1", pokemon.fast_attack.dps)
            setattr(pokemon, "dps2", pokemon.charged_attack.dps)
            setattr(pokemon, "dps_attack", pokemon.moveset.dps_attack)
            setattr(pokemon, "dps_defense", pokemon.moveset.dps_defense)
            setattr(pokemon, "attack_perfection", pokemon.moveset.attack_perfection)
            setattr(pokemon, "defense_perfection", pokemon.moveset.defense_perfection)

        self.ongoing_stardust_count = self.bot.stardust

    def get_colorlist_names(self, names):
        whitelist_names = []
        blacklist_names = []

        for name in names:
            if not name:
                continue

            if name[0] not in ['!', '-']:
                group_names = self.config_groups.get(name, [])

                if not group_names:
                    name = self.get_closest_name(name)

                if name:
                    whitelist_names.append(name)
                    whitelist_subnames, blacklist_subnames = self.get_colorlist_names(group_names)
                    whitelist_names += whitelist_subnames
                    blacklist_names += blacklist_subnames
            else:
                name = name[1:]
                group_names = self.config_groups.get(name, [])

                if not group_names:
                    name = self.get_closest_name(name)

                if name:
                    blacklist_names.append(name)
                    blacklist_subnames, whitelist_subnames = self.get_colorlist_names(group_names)
                    blacklist_names += blacklist_subnames
                    whitelist_names += whitelist_subnames

        return (whitelist_names, blacklist_names)

    def get_family_names(self, family_id):
        ids = [family_id]
        ids += inventory.pokemons().data_for(family_id).next_evolutions_all[:]
        return [inventory.pokemons().name_for(x) for x in ids]

    def get_closest_name(self, name):
        closest_names = difflib.get_close_matches(name, self.pokemon_names, 1)

        if closest_names:
            closest_name = closest_names[0]

            if name != closest_name:
                self.logger.warning("Unknown Pokemon name [%s]. Assuming it is [%s]", name, closest_name)

            return closest_name
        else:
            raise ConfigException("Unknown Pokemon name [%s]" % name)

    def group_by_pokemon_id(self, pokemon_list):
        sorted_list = sorted(pokemon_list, key=self.get_pokemon_id)
        return itertools.groupby(sorted_list, self.get_pokemon_id)

    def group_by_family_id(self, pokemon_list):
        sorted_list = sorted(pokemon_list, key=self.get_family_id)
        return itertools.groupby(sorted_list, self.get_family_id)

    def get_pokemon_id(self, pokemon):
        return pokemon.pokemon_id

    def get_family_id(self, pokemon):
        return pokemon.first_evolution_id

    def get_best_pokemon_for_rule(self, pokemon_list, rule):
        sorted_pokemon = self.sort_pokemon_list_to_keep(pokemon_list, rule)

        if len(sorted_pokemon) == 0:
            return ([], [], [])

        top = max(rule.get("top", 0), 0)
        index = int(math.ceil(top)) - 1

        if 0 < top < 1:
            worst = object()

            for a in rule.get("sort", []):
                best_attribute = getattr(sorted_pokemon[0], a)
                setattr(worst, a, best_attribute * (1 - top))
        elif 0 <= index < len(sorted_pokemon):
            worst = sorted_pokemon[index]
        else:
            worst = sorted_pokemon[-1]

        return self.get_better_pokemon_for_rule(sorted_pokemon, rule, worst)

    def get_multi_best_pokemon_for_rule(self, family_list, rule, nb_branch):
        sorted_family = self.sort_pokemon_list_to_keep(family_list, rule)

        # Handle each group of senior independently
        senior_pokemon_list = [p for p in sorted_family if not p.has_next_evolution()]
        other_family_list = [p for p in sorted_family if p.has_next_evolution()]
        senior_pids = set(p.pokemon_id for p in senior_pokemon_list)

        keep_all = []
        try_evolve_all = []
        try_upgrade_all = []

        if not self.config_evolve:
            # Player handle evolution manually = Fall-back to per Pokemon behavior
            for _, pokemon_list in self.group_by_pokemon_id(sorted_family):
                keep, try_evolve, try_upgrade = self.get_best_pokemon_for_rule(pokemon_list, rule)
                keep_all += keep
                try_evolve_all += try_evolve
                try_upgrade_all += try_upgrade
        else:
            for _, pokemon_list in self.group_by_pokemon_id(senior_pokemon_list):
                keep, try_evolve, try_upgrade = self.get_best_pokemon_for_rule(pokemon_list, rule)
                keep_all += keep
                try_evolve_all += try_evolve
                try_upgrade_all += try_upgrade

            if len(other_family_list) > 0:
                if len(senior_pids) < nb_branch:
                    # We did not get every combination yet = All other Pokemon are potentially good to keep
                    worst = other_family_list[-1]
                else:
                    best = keep_all + try_evolve_all + try_upgrade_all
                    worst = self.sort_pokemon_list_to_keep(best, rule)[-1]

                keep, try_evolve, try_upgrade = self.get_better_pokemon_for_rule(other_family_list, rule, worst, 12)
                keep_all += keep
                try_evolve_all += try_evolve
                try_upgrade_all += try_upgrade

        return keep_all, try_evolve_all, try_upgrade_all

    def get_better_pokemon_for_rule(self, pokemon_list, rule, worst, limit=1000):
        min_score = self.get_score(worst, rule)[0]
        scored_list = [(p, self.get_score(p, rule)) for p in pokemon_list]
        scored_keep = [x for x in scored_list if (x[1][0] >= min_score) and (x[1][1] is True)][:limit]
        keep = [x[0] for x in scored_keep]
        try_evolve = [x[0] for x in scored_keep if x[1][2] is True]
        try_upgrade = [x[0] for x in scored_keep if (x[1][2] is False) and (x[1][3] is True)]

        return keep, try_evolve, try_upgrade

    def sort_pokemon_list_to_keep(self, pokemon_list, rule):
        scored_list = [(p, self.get_score(p, rule)) for p in pokemon_list]
        scored_keep = [x for x in scored_list if x[1][1] is True]
        scored_keep.sort(key=lambda x: x[1][0], reverse=True)

        return [p for p, x in scored_keep]

    def get_score(self, pokemon, rule):
        score = []

        for a in rule.get("sort", []):
            value = getattr(pokemon, a, 0)
            score.append(value)

        rule_keep = rule.get("keep", True)
        rule_evolve = rule.get("evolve", True)
        rule_upgrade = rule.get("upgrade", False)

        keep = rule_keep not in [False, {}]
        keep &= self.satisfy_requirements(pokemon, rule_keep)

        may_try_evolve = (hasattr(pokemon, "has_next_evolution") and pokemon.has_next_evolution())
        may_try_evolve &= rule_evolve not in [False, {}]
        may_try_evolve &= self.satisfy_requirements(pokemon, rule_evolve)

        may_try_upgrade = rule_upgrade not in [False, {}]
        may_try_upgrade &= self.satisfy_requirements(pokemon, rule_upgrade)

        return tuple(score), keep, may_try_evolve, may_try_upgrade

    def satisfy_requirements(self, pokemon, req):
        if type(req) is bool:
            return req

        satisfy = True

        for a, v in req.items():
            value = getattr(pokemon, a, 0)

            if (type(v) is str) or (type(v) is unicode):
                v = float(v)

            if type(v) is list:
                if type(v[0]) is list:
                    satisfy_range = False

                    for r in v:
                        satisfy_range |= (value >= r[0]) and (value <= r[1])

                    satisfy &= satisfy_range
                else:
                    satisfy &= (value >= v[0]) and (value <= v[1])
            elif v < 0:
                satisfy &= (value <= abs(v))
            else:
                satisfy &= (value >= v)

        return satisfy

    def unique_pokemon_list(self, pokemon_list):
        seen = set()
        return [p for p in pokemon_list if not (p.unique_id in seen or seen.add(p.unique_id))]

    def get_evolution_plan(self, family_id, family_list, keep, try_evolve, try_upgrade):
        candies = inventory.candies().get(family_id).quantity

        # All the rest is crap, for now
        crap = list(family_list)
        crap = [p for p in crap if p not in keep]
        crap = [p for p in crap if not p.in_fort and not p.is_favorite]
        crap.sort(key=lambda p: (p.iv, p.cp), reverse=True)

        # We will gain a candy whether we choose to transfer or evolve these Pokemon
        candies += len(crap)

        evolve = []

        for pokemon in try_evolve:
            candies -= pokemon.evolution_cost

            if candies < 0:
                continue

            candies += 1
            evolve.append(pokemon)

        upgrade = []
        upgrade_level = min(self.config_upgrade_level, inventory.player().level * 2)

        for pokemon in try_upgrade:
            level = int(pokemon.level * 2) - 1

            if level >= upgrade_level:
                continue

            full_upgrade_candy_cost = 0
            full_upgrade_stardust_cost = 0

            for i in range(level, upgrade_level):
                upgrade_cost = self.pokemon_upgrade_cost[i - 1]
                full_upgrade_candy_cost += upgrade_cost[0]
                full_upgrade_stardust_cost += upgrade_cost[1]

            candies -= full_upgrade_candy_cost
            self.ongoing_stardust_count -= full_upgrade_stardust_cost

            if (candies < 0) or (self.ongoing_stardust_count < 0):
                continue

            upgrade.append(pokemon)

        if self.config_evolve_for_xp:
            # Compute how many crap we should keep if we want to batch evolve them for xp
            lowest_evolution_cost = inventory.pokemons().evolution_cost_for(family_id)

            # transfer + keep_for_xp = len(crap)
            # leftover_candies = candies - len(crap) + transfer * 1
            # keep_for_xp = (leftover_candies - 1) / (lowest_evolution_cost - 1)
            # keep_for_xp = (candies - len(crap) + transfer - 1) / (lowest_evolution_cost - 1)
            # keep_for_xp = (candies - keep_for_xp - 1) / (lowest_evolution_cost - 1)

            if (candies > 0) and lowest_evolution_cost:
                keep_for_xp = int((candies - 1) / lowest_evolution_cost)
            else:
                keep_for_xp = 0

            xp = [p for p in crap if p.has_next_evolution() and p.evolution_cost == lowest_evolution_cost][:keep_for_xp]

            # If not much to evolve, better keep the candies
            if len(xp) < math.ceil(self.max_pokemon_storage * 0.02):
                xp = []

            transfer = [p for p in crap if p not in xp]
        else:
            xp = []
            transfer = crap

        return (transfer, evolve, upgrade, xp)

    def apply_optimization(self, transfer, evolve, upgrade, xp):
        transfer_count = len(transfer)
        evolve_count = len(evolve)
        upgrade_count = len(upgrade)
        xp_count = len(xp)

        if transfer_count > 0:
            self.logger.info("Transferring %s Pokemon", transfer_count)

            for pokemon in transfer:
                self.transfer_pokemon(pokemon)

        evolve_xp_count = evolve_count + xp_count

        if evolve_xp_count > 0:
            skip_evolve = False

            if self.config_evolve and self.config_may_use_lucky_egg and (not self.bot.config.test):
                lucky_egg = inventory.items().get(Item.ITEM_LUCKY_EGG.value)  # @UndefinedVariable

                if lucky_egg.count == 0:
                    if self.config_evolve_only_with_lucky_egg:
                        skip_evolve = True
                        self.emit_event("skip_evolve",
                                        formatted="Skipping evolution step. No lucky egg available")
                elif evolve_xp_count < self.config_evolve_count_for_lucky_egg:
                    if self.config_evolve_only_with_lucky_egg:
                        skip_evolve = True
                        self.emit_event("skip_evolve",
                                        formatted="Skipping evolution step. Not enough Pokemon to evolve with lucky egg: %s/%s" % (evolve_xp_count, self.config_evolve_count_for_lucky_egg))
                    elif self.get_pokemon_slot_left() > self.config_min_slots_left:
                        skip_evolve = True
                        self.emit_event("skip_evolve",
                                        formatted="Waiting for more Pokemon to evolve with lucky egg: %s/%s" % (evolve_xp_count, self.config_evolve_count_for_lucky_egg))
                else:
                    self.use_lucky_egg()

            if not skip_evolve:
                if evolve_count > 0:
                    self.logger.info("Evolving %s Pokemon (the best)", evolve_count)

                    for pokemon in evolve:
                        self.evolve_pokemon(pokemon)

                if xp_count > 0:
                    self.logger.info("Evolving %s Pokemon (for xp)", xp_count)

                    for pokemon in xp:
                        self.evolve_pokemon(pokemon)

        if upgrade_count > 0:
            self.logger.info("Upgrading %s Pokemon [%s stardust]", upgrade_count, self.bot.stardust)

            for pokemon in upgrade:
                self.upgrade_pokemon(pokemon)

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
            response_dict = {"responses": {"EVOLVE_POKEMON": {"result": SUCCESS}}}

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
            inventory.player().exp += xp

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

            sleep(self.config_evolve_time, 0.1)

        return True

    def upgrade_pokemon(self, pokemon):
        level = int(pokemon.level * 2) - 1
        upgrade_level = min(self.config_upgrade_level, inventory.player().level * 2)
        candy = inventory.candies().get(pokemon.pokemon_id)

        for i in range(level, upgrade_level):
            upgrade_cost = self.pokemon_upgrade_cost[i - 1]
            upgrade_candy_cost = upgrade_cost[0]
            upgrade_stardust_cost = upgrade_cost[1]

            if self.config_upgrade and (not self.bot.config.test):
                response_dict = self.bot.api.upgrade_pokemon(pokemon_id=pokemon.unique_id)
            else:
                response_dict = {"responses": {"UPGRADE_POKEMON": {"result": SUCCESS}}}

            if not response_dict:
                return False

            result = response_dict.get("responses", {}).get("UPGRADE_POKEMON", {}).get("result", 0)

            if result != SUCCESS:
                return False

            upgrade = response_dict.get("responses", {}).get("UPGRADE_POKEMON", {}).get("upgraded_pokemon", {})

            if self.config_upgrade and (not self.bot.config.test):
                candy.consume(upgrade_candy_cost)
                self.bot.stardust -= upgrade_stardust_cost

            self.emit_event("pokemon_upgraded",
                            formatted="Upgraded {pokemon} [IV {iv}] [CP {cp}] [{candy} candies] [{stardust} stardust]",
                            data={"pokemon": pokemon.name,
                                  "iv": pokemon.iv,
                                  "cp": pokemon.cp,
                                  "candy": candy.quantity,
                                  "stardust": self.bot.stardust})

            if self.config_upgrade and (not self.bot.config.test):
                inventory.pokemons().remove(pokemon.unique_id)

                new_pokemon = inventory.Pokemon(upgrade)
                inventory.pokemons().add(new_pokemon)

                action_delay(self.config_transfer_wait_min, self.config_transfer_wait_max)

        return True
