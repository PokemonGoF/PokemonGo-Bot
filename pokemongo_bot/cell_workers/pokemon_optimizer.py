import copy
import logging

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot.item_list import Item
from pokemongo_bot.worker_result import WorkerResult


class PokemonOptimizer(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.family_by_family_id = {}
        self.logger = logging.getLogger(self.__class__.__name__)

        self.config_transfer = self.config.get("transfer", False)
        self.config_evolve = self.config.get("evolve", False)
        self.config_use_candies_for_xp = self.config.get("use_candies_for_xp", True)
        self.config_use_lucky_egg = self.config.get("use_lucky_egg", False)
        self.config_evolve_only_with_lucky_egg = self.config.get("evolve_only_with_lucky_egg", True)
        self.config_minimum_evolve_for_lucky_egg = self.config.get("minimum_evolve_for_lucky_egg", 90)
        self.config_keep = self.config.get("keep", [{"top": 1, "evolve": True, "sort": ["iv"]},
                                                    {"top": 1, "evolve": True, "sort": ["ncp"]},
                                                    {"top": 1, "evolve": False, "sort": ["cp"]}])

    def get_pokemon_slot_left(self):
        return self.bot._player["max_pokemon_storage"] - len(inventory.pokemons()._data)

    def work(self):
        if self.get_pokemon_slot_left() > 5:
            return WorkerResult.SUCCESS

        self.parse_inventory()

        transfer_all = []
        evo_all_best = []
        evo_all_crap = []

        for family_id, family in self.family_by_family_id.items():
            transfer, evo_best, evo_crap = self.get_family_optimized(family_id, family)
            transfer_all += transfer
            evo_all_best += evo_best
            evo_all_crap += evo_crap

        evo_all = evo_all_best + evo_all_crap

        self.apply_optimization(transfer_all, evo_all)
        inventory.refresh_inventory()

        return WorkerResult.SUCCESS

    def parse_inventory(self):
        self.family_by_family_id.clear()

        for pokemon in inventory.pokemons().all():
            family_id = pokemon.first_evolution_id
            setattr(pokemon, "ncp", pokemon.cp_percent)
            setattr(pokemon, "dps", pokemon.moveset.dps)
            setattr(pokemon, "dps_attack", pokemon.moveset.dps_attack)
            setattr(pokemon, "dps_defense", pokemon.moveset.dps_defense)

            self.family_by_family_id.setdefault(family_id, []).append(pokemon)

    def get_family_optimized(self, family_id, family):
        if family_id == 133:  # "Eevee"
            return self.get_multi_family_optimized(family_id, family, 3)

        evolve_best = []
        keep_best = []

        for criteria in self.config_keep:
            if criteria.get("evolve", True):
                evolve_best += self.get_top_rank(family, criteria)
            else:
                keep_best += self.get_top_rank(family, criteria)

        evolve_best = self.unique_pokemons(evolve_best)
        keep_best = self.unique_pokemons(keep_best)

        return self.get_evolution_plan(family_id, family, evolve_best, keep_best)

    def get_multi_family_optimized(self, family_id, family, nb_branch):
        # Transfer each group of senior independently
        senior_family = [p for p in family if not p.has_next_evolution()]
        other_family = [p for p in family if p.has_next_evolution()]
        senior_pids = set(p.pokemon_id for p in senior_family)
        senior_grouped_family = {pid: [p for p in senior_family if p.pokemon_id == pid] for pid in senior_pids}

        transfer_senior = []

        for senior_pid, senior_family in senior_grouped_family.items():
            transfer_senior += self.get_family_optimized(senior_pid, senior_family)[0]

        if len(senior_pids) < nb_branch:
            # We did not get every combination yet = All other Pokemons are potentially good to keep
            evolve_best = other_family
            evolve_best.sort(key=lambda p: p.iv * p.ncp, reverse=True)
            keep_best = []
        else:
            evolve_best = []
            keep_best = []

            for criteria in self.config_keep:
                top = []

                for f in senior_grouped_family.values():
                    top += self.get_top_rank(f, criteria)

                worst = self.get_sorted_family(top, criteria)[-1]

                if criteria.get("evolve", True):
                    evolve_best += self.get_better_rank(family, criteria, worst)
                else:
                    keep_best += self.get_better_rank(family, criteria, worst)

            evolve_best = self.unique_pokemons(evolve_best)
            keep_best = self.unique_pokemons(keep_best)

        transfer, evo_best, evo_crap = self.get_evolution_plan(family_id, other_family, evolve_best, keep_best)
        transfer += transfer_senior

        return (transfer, evo_best, evo_crap)

    def get_top_rank(self, family, criteria):
        sorted_family = self.get_sorted_family(family, criteria)
        worst = sorted_family[criteria.get("top", 1) - 1]
        return [p for p in sorted_family if self.get_rank(p, criteria) >= self.get_rank(worst, criteria)]

    def get_better_rank(self, family, criteria, worst):
        return [p for p in self.get_sorted_family(family, criteria) if self.get_rank(p, criteria) >= self.get_rank(worst, criteria)]

    def get_sorted_family(self, family, criteria):
        return sorted(family, key=lambda p: self.get_rank(p, criteria), reverse=True)

    def get_rank(self, pokemon, criteria):
        return tuple(getattr(pokemon, a, None) for a in criteria.get("sort"))

    def get_pokemon_max_cp(self, pokemon_name):
        return int(self.pokemon_max_cp.get(pokemon_name, 0))

    def unique_pokemons(self, l):
        seen = set()
        return [p for p in l if not (p.id in seen or seen.add(p.id))]

    def get_evolution_plan(self, family_id, family, evolve_best, keep_best):
        candies = inventory.candies().get(family_id).quantity

        # All the rest is crap, for now
        crap = family[:]
        crap = [p for p in crap if p not in evolve_best]
        crap = [p for p in crap if p not in keep_best]
        crap.sort(key=lambda p: p.iv, reverse=True)

        candies += len(crap)

        # Let's see if we can evolve our best pokemons
        can_evolve_best = []

        for pokemon in evolve_best:
            if not pokemon.has_next_evolution():
                continue

            candies -= pokemon.evolution_cost

            if candies < 0:
                continue

            can_evolve_best.append(pokemon)

            # Not sure if the evo keep the same id
            next_pid = pokemon.next_evolution_ids[0]
            next_evo = copy.copy(pokemon)
            next_evo.pokemon_id = next_pid
            next_evo._static_data = inventory.pokemons().data_for(next_pid)
            next_evo.name = inventory.pokemons().name_for(next_pid)
            evolve_best.append(next_evo)

        if self.config_use_candies_for_xp:
            # Compute how many crap we should keep if we want to batch evolve them for xp
            junior_evolution_cost = inventory.pokemons().evolution_cost_for(family_id)

            # transfer + keep_for_evo = len(crap)
            # leftover_candies = candies - len(crap) + transfer * 1
            # keep_for_evo = leftover_candies / junior_evolution_cost
            #
            # keep_for_evo = (candies - len(crap) + transfer) / junior_evolution_cost
            # keep_for_evo = (candies - keep_for_evo) / junior_evolution_cost

            if (candies > 0) and junior_evolution_cost:
                keep_for_evo = int(candies / (junior_evolution_cost + 1))
            else:
                keep_for_evo = 0

            evo_crap = [p for p in crap if p.has_next_evolution() and p.evolution_cost == junior_evolution_cost][:keep_for_evo]
            transfer = [p for p in crap if p not in evo_crap]
        else:
            evo_crap = []
            transfer = crap

        return (transfer, can_evolve_best, evo_crap)

    def apply_optimization(self, transfer, evo):
        for pokemon in transfer:
            self.transfer_pokemon(pokemon)

        if len(evo) == 0:
            return

        if self.config_evolve and self.config_use_lucky_egg and (not self.bot.config.test):
            lucky_egg = inventory.items().get(Item.ITEM_LUCKY_EGG.value)  # @UndefinedVariable

            if self.config_evolve_only_with_lucky_egg and (lucky_egg.count == 0):
                self.logger.info("Skipping evolution step. No lucky egg available")
                return

            if len(evo) < self.config_minimum_evolve_for_lucky_egg:
                self.logger.info("Skipping evolution step. Not enough Pokemons (%s) to evolve", len(evo))
                return

            self.use_lucky_egg()

        self.logger.info("Evolving %s Pokemons", len(evo))

        for pokemon in evo:
            self.evolve_pokemon(pokemon)

    def transfer_pokemon(self, pokemon):
        if self.config_transfer and (not self.bot.config.test):
            response_dict = self.bot.api.release_pokemon(pokemon_id=pokemon.id)
        else:
            response_dict = {"responses": {"RELEASE_POKEMON": {"candy_awarded": 0}}}

        if not response_dict:
            return False

        self.emit_event("pokemon_release",
                        formatted="Exchanged {pokemon} [IV {iv}] [CP {cp}] [NCP {ncp}] [DPS {dps}]",
                        data={"pokemon": pokemon.name,
                              "iv": pokemon.iv,
                              "cp": pokemon.cp,
                              "ncp": round(pokemon.ncp, 2),
                              "dps": round(pokemon.dps, 2)})

        if self.config_transfer and (not self.bot.config.test):
            candy = response_dict.get("responses", {}).get("RELEASE_POKEMON", {}).get("candy_awarded", 0)

            inventory.candies().get(pokemon.pokemon_id).add(candy)
            inventory.pokemons().remove(pokemon.id)

            action_delay(self.bot.config.action_wait_min, self.bot.config.action_wait_max)

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

        if result == 1:
            lucky_egg.remove(1)

            self.emit_event("used_lucky_egg",
                            formatted="Used lucky egg ({amount_left} left).",
                            data={"amount_left": lucky_egg.count})
            return True
        else:
            self.emit_event("lucky_egg_error",
                            level='error',
                            formatted="Failed to use lucky egg!")
            return False

    def evolve_pokemon(self, pokemon):
        if self.config_evolve and (not self.bot.config.test):
            response_dict = self.bot.api.evolve_pokemon(pokemon_id=pokemon.id)
        else:
            response_dict = {"responses": {"EVOLVE_POKEMON": {"result": 1}}}

        if not response_dict:
            return False

        result = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("result", 0)

        if result != 1:
            return False

        xp = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("experience_awarded", 0)
        candy = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("candy_awarded", 0)
        evolution = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("evolved_pokemon_data", {})

        self.emit_event("pokemon_evolved",
                        formatted="Evolved {pokemon} [IV {iv}] [CP {cp}] [NCP {ncp}] [DPS {dps}] [+{xp} xp]",
                        data={"pokemon": pokemon.name,
                              "iv": pokemon.iv,
                              "cp": pokemon.cp,
                              "ncp": round(pokemon.ncp, 2),
                              "dps": round(pokemon.dps, 2),
                              "xp": xp})

        if self.config_evolve and (not self.bot.config.test):
            inventory.candies().get(pokemon.pokemon_id).consume(pokemon.evolution_cost - candy)
            inventory.pokemons().remove(pokemon.id)

            new_pokemon = inventory.Pokemon(evolution)
            inventory.pokemons().add(new_pokemon)

            sleep(20)

        return True
