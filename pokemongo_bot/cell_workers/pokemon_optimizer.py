import copy

from pokemongo_bot import inventory
from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot.item_list import Item
from pokemongo_bot.worker_result import WorkerResult


class PokemonOptimizer(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.pokemon_max_cp = {}
        self.family_by_family_id = {}

        self.init_pokemon_max_cp()

        self.dry_run = self.config.get("dry_run", True)
        self.evolve_only_with_lucky_egg = self.config.get("evolve_only_with_lucky_egg", True)

    def get_pokemon_slot_left(self):
        return self.bot._player["max_pokemon_storage"] - len(inventory.pokemons()._data)

    def work(self):
        self.refresh_inventory()

        if self.get_pokemon_slot_left() > 5:
            return WorkerResult.SUCCESS

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

    def get_family_optimized(self, family_id, family):
        if family_id == 133:  # "Eevee"
            return self.get_multi_family_optimized(family_id, family, 3)

        best_iv = self.get_best_iv_in_family(family)
        best_relative_cp = self.get_best_relative_cp_in_family(family)
        best_cp = self.get_best_cp_in_family(family)

        best = self.combine_pokemon_lists(best_iv, best_relative_cp)

        return self.get_evolution_plan(family_id, family, best, best_cp)

    def get_multi_family_optimized(self, family_id, family, nb_branch):
        # Transfer each group of senior independently
        senior_family = [p for p in family if p.next_evolution_id is None]
        other_family = [p for p in family if p.next_evolution_id is not None]
        senior_pids = set(p.pokemon_id for p in senior_family)
        senior_grouped_family = {pid: [p for p in senior_family if p.pokemon_id == pid] for pid in senior_pids}

        transfer_senior = []

        for senior_pid, senior_family in senior_grouped_family.items():
            transfer_senior += self.get_family_optimized(senior_pid, senior_family)[0]

        if len(senior_pids) < nb_branch:
            # We did not get every combination yet = All other Pokemons are potentially good to keep
            best = other_family
            best.sort(key=lambda p: p.iv * p.relative_cp, reverse=True)
            best_cp = []
        else:
            min_iv = min([max(f, key=lambda p: p.iv) for f in senior_grouped_family.values()], key=lambda p: p.iv).iv
            min_relative_cp = min([max(f, key=lambda p: p.relative_cp) for f in senior_grouped_family.values()], key=lambda p: p.relative_cp).relative_cp
            min_cp = min([max(f, key=lambda p: p.cp) for f in senior_grouped_family.values()], key=lambda p: p.cp).cp

            best_iv = self.get_better_iv_in_family(other_family, min_iv)
            best_relative_cp = self.get_better_relative_cp_in_family(other_family, min_relative_cp)
            best_cp = self.get_better_cp_in_family(other_family, min_cp)

            best = self.combine_pokemon_lists(best_iv, best_relative_cp)

        transfer, evo_best, evo_crap = self.get_evolution_plan(family_id, other_family, best, best_cp)
        transfer += transfer_senior

        return (transfer, evo_best, evo_crap)

    def get_evolution_plan(self, family_id, family, best, best_cp):
        candies = inventory.candies().get(family_id).quantity

        # All the rest is crap, for now
        crap = family[:]
        crap = [p for p in crap if p not in best]
        crap = [p for p in crap if p not in best_cp]
        crap.sort(key=lambda p: p.iv, reverse=True)

        candies += len(crap)

        # Let's see if we can evolve our best pokemons
        evo_best = []

        for pokemon in best:
            if not pokemon.has_next_evolution():
                continue

            candies -= pokemon.evolution_cost

            if candies < 0:
                continue

            evo_best.append(pokemon)

            # Not sure if the evo keep the same id
            next_pid = pokemon.next_evolution_id
            next_evo = copy.copy(pokemon)
            next_evo.pokemon_id = next_pid
            next_evo._static_data = inventory.pokemons().data_for(next_pid)
            next_evo.name = inventory.pokemons().name_for(next_pid)
            best.append(next_evo)

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

        return (transfer, evo_best, evo_crap)

    def apply_optimization(self, transfer, evo):
        for pokemon in transfer:
            self.transfer_pokemon(pokemon)

        if self.evolve_only_with_lucky_egg:
            try:
                lucky_egg_count = inventory.items().count_for(Item.ITEM_LUCKY_EGG)
            except:
                lucky_egg_count = 0

            if (lucky_egg_count == 0) or (len(evo) < 90):
                return

            self.use_lucky_egg()

        for pokemon in evo:
            self.evolve_pokemon(pokemon)

    def get_best_iv_in_family(self, family):
        best = max(family, key=lambda p: p.iv)
        return sorted([p for p in family if p.iv == best.iv], key=lambda p: p.relative_cp, reverse=True)

    def get_better_iv_in_family(self, family, iv):
        return sorted([p for p in family if p.iv >= iv], key=lambda p: (p.iv, p.relative_cp), reverse=True)

    def get_best_relative_cp_in_family(self, family):
        best = max(family, key=lambda p: p.relative_cp)
        return sorted([p for p in family if p.relative_cp == best.relative_cp], key=lambda p: p.iv, reverse=True)

    def get_better_relative_cp_in_family(self, family, relative_cp):
        return sorted([p for p in family if p.relative_cp >= relative_cp], key=lambda p: (p.relative_cp, p.iv), reverse=True)

    def get_best_cp_in_family(self, family):
        best = max(family, key=lambda p: p.cp)
        return sorted([p for p in family if p.cp == best.cp], key=lambda p: (p.relative_cp, p.iv), reverse=True)

    def get_better_cp_in_family(self, family, cp):
        return sorted([p for p in family if p.cp >= cp], key=lambda p: (p.relative_cp, p.iv), reverse=True)

    def transfer_pokemon(self, pokemon):
        if self.dry_run:
            pass
        else:
            self.bot.api.release_pokemon(pokemon_id=pokemon.id)

        self.emit_event("pokemon_release",
                        formatted="Exchanged {pokemon} [IV {iv}] [CP {cp}]",
                        data={"pokemon": pokemon.name,
                              "iv": pokemon.iv,
                              "cp": pokemon.cp})

        if not self.dry_run:
            inventory.candies().get(pokemon.pokemon_id).add(1)
            action_delay(self.bot.config.action_wait_min, self.bot.config.action_wait_max)

    def use_lucky_egg(self):
        if self.dry_run:
            response_dict = {"responses": {"USE_ITEM_XP_BOOST": {"result": 1}}}
        else:
            response_dict = self.bot.use_lucky_egg()

        if not response_dict:
            self.emit_event("lucky_egg_error",
                            level='error',
                            formatted="Failed to use lucky egg!")
            return False

        result = response_dict.get("responses", {}).get("USE_ITEM_XP_BOOST", {}).get("result", 0)

        if result == 1:
            self.emit_event("used_lucky_egg",
                            formatted="Used lucky egg ({amount_left} left).",
                            data={"amount_left": 0})
            return True
        else:
            self.emit_event("lucky_egg_error",
                            level='error',
                            formatted="Failed to use lucky egg!")
            return False

    def evolve_pokemon(self, pokemon):
        if self.dry_run:
            response_dict = {"responses": {"EVOLVE_POKEMON": {"result": 1}}}
        else:
            response_dict = self.bot.api.evolve_pokemon(pokemon_id=pokemon.id)

        if not response_dict:
            return False

        result = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("result", 0)
        xp = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("experience_awarded", 0)

        if result == 1:
            self.emit_event("pokemon_evolved",
                            formatted="Evolved {pokemon} [IV {iv}] [CP {cp}] [+{xp} xp]",
                            data={"pokemon": pokemon.name,
                                  "iv": pokemon.iv,
                                  "cp": pokemon.cp,
                                  "xp": xp})

            if not self.dry_run:
                inventory.candies().get(pokemon.pokemon_id).consume(pokemon.evolution_cost)
                sleep(20)

            return True
        else:
            return False

    def refresh_inventory(self):
        self.family_by_family_id.clear()

        for pokemon in inventory.pokemons().all():
            family_id = pokemon.first_evolution_id

            max_cp = self.get_pokemon_max_cp(pokemon.name)

            if max_cp > 0:
                relative_cp = float(pokemon.cp) / max_cp
            else:
                relative_cp = 0

            setattr(pokemon, "relative_cp", relative_cp)

            self.family_by_family_id.setdefault(family_id, []).append(pokemon)

    def get_pokemon_max_cp(self, pokemon_name):
        return int(self.pokemon_max_cp.get(pokemon_name, 0))

    def combine_pokemon_lists(self, a, b):
        seen = set()
        return [p for p in a + b if not (p.id in seen or seen.add(p.id))]

    def init_pokemon_max_cp(self):
        self.pokemon_max_cp = {
            "Bulbasaur": 1072, "Ivysaur": 1632, "Venusaur": 2580, "Charmander": 955, "Charmeleon": 1557,
            "Charizard": 2602, "Squirtle": 1009, "Wartortle": 1583, "Blastoise": 2542, "Caterpie": 444,
            "Metapod": 478, "Butterfree": 1455, "Weedle": 449, "Kakuna": 485, "Beedrill": 1440,
            "Pidgey": 680, "Pidgeotto": 1224, "Pidgeot": 2091, "Rattata": 582, "Raticate": 1444,
            "Spearow": 687, "Fearow": 1746, "Ekans": 824, "Arbok": 1767, "Pikachu": 888,
            "Raichu": 2028, "Sandshrew": 799, "Sandslash": 1810, "Nidoran F": 876, "Nidorina": 1405,
            "Nidoqueen": 2485, "Nidoran M": 843, "Nidorino": 1373, "Nidoking": 2475, "Clefairy": 1201,
            "Clefable": 2398, "Vulpix": 831, "Ninetales": 2188, "Jigglypuff": 918, "Wigglytuff": 2177,
            "Zubat": 643, "Golbat": 1921, "Oddish": 1148, "Gloom": 1689, "Vileplume": 2493,
            "Paras": 917, "Parasect": 1747, "Venonat": 1029, "Venomoth": 1890, "Diglett": 457,
            "Dugtrio": 1169, "Meowth": 756, "Persian": 1632, "Psyduck": 1110, "Golduck": 2387,
            "Mankey": 879, "Primeape": 1865, "Growlithe": 1335, "Arcanine": 2984, "Poliwag": 796,
            "Poliwhirl": 1340, "Poliwrath": 2505, "Abra": 600, "Kadabra": 1132, "Alakazam": 1814,
            "Machop": 1090, "Machoke": 1761, "Machamp": 2594, "Bellsprout": 1117, "Weepinbell": 1724,
            "Victreebel": 2531, "Tentacool": 905, "Tentacruel": 2220, "Geodude": 849, "Graveler": 1434,
            "Golem": 2303, "Ponyta": 1516, "Rapidash": 2199, "Slowpoke": 1219, "Slowbro": 2597,
            "Magnemite": 891, "Magneton": 1880, "Farfetch'd": 1264, "Doduo": 855, "Dodrio": 1836,
            "Seel": 1107, "Dewgong": 2146, "Grimer": 1284, "Muk": 2603, "Shellder": 823,
            "Cloyster": 2053, "Gastly": 804, "Haunter": 1380, "Gengar": 2078, "Onix": 857,
            "Drowzee": 1075, "Hypno": 2184, "Krabby": 792, "Kingler": 1823, "Voltorb": 840,
            "Electrode": 1646, "Exeggcute": 1100, "Exeggutor": 2955, "Cubone": 1007, "Marowak": 1657,
            "Hitmonlee": 1493, "Hitmonchan": 1517, "Lickitung": 1627, "Koffing": 1152, "Weezing": 2250,
            "Rhyhorn": 1182, "Rhydon": 2243, "Chansey": 675, "Tangela": 1740, "Kangaskhan": 2043,
            "Horsea": 795, "Seadra": 1713, "Goldeen": 965, "Seaking": 2044, "Staryu": 938,
            "Starmie": 2182, "Mr. Mime": 1494, "Scyther": 2074, "Jynx": 1717, "Electabuzz": 2119,
            "Magmar": 2265, "Pinsir": 2122, "Tauros": 1845, "Magikarp": 263, "Gyarados": 2689,
            "Lapras": 2981, "Ditto": 920, "Eevee": 1077, "Vaporeon": 2816, "Jolteon": 2140,
            "Flareon": 2643, "Porygon": 1692, "Omanyte": 1120, "Omastar": 2234, "Kabuto": 1105,
            "Kabutops": 2130, "Aerodactyl": 2165, "Snorlax": 3113, "Articuno": 2978, "Zapdos": 3114,
            "Moltres": 3240, "Dratini": 983, "Dragonair": 1748, "Dragonite": 3500, "Mewtwo": 4145,
            "Mew": 3299}
