import logging

from pokemongo_bot.base_task import BaseTask
from pokemongo_bot.human_behaviour import sleep, action_delay
from pokemongo_bot.item_list import Item


class PokemonOptimizer(BaseTask):
    SUPPORTED_TASK_API_VERSION = 1

    def initialize(self):
        self.player_level_factor = None
        self.pokemon_max_cp = None
        self.family_data_by_pokemon_name = {}

        self.init_player_level_factor()
        self.init_pokemon_max_cp()
        self.init_family_data_by_pokemon_name()

        self.family_by_family_name = {}
        self.candies_by_family_name = {}
        self.pokemon_count = 0
        self.lucky_egg_count = 0

        self.dry_run = self.config.get("dry_run", True)
        self.use_lucky_egg = self.config.get("use_lucky_egg", True)

    def get_pokemon_slot_left(self):
        return self.bot._player["max_pokemon_storage"] - self.pokemon_count

    def work(self):
        family_changed = True

        while family_changed:
            family_changed = False

            self.refresh_inventory()

            if self.get_pokemon_slot_left() > 5:
                break

            transfer_all_pokemons = []
            evo_all_best_pokemons = []
            evo_all_crap_pokemons = []

            for family_name, family in self.family_by_family_name.items():
                transfer_pokemons, evo_best_pokemons, evo_crap_pokemons = self.get_family_optimized(family_name, family)
                transfer_all_pokemons += transfer_pokemons
                evo_all_best_pokemons += evo_best_pokemons
                evo_all_crap_pokemons += evo_crap_pokemons

            evo_all_pokemons = evo_all_best_pokemons + evo_all_crap_pokemons

            family_changed = self.apply_optimization(transfer_all_pokemons, evo_all_pokemons)

            if self.dry_run:
                break

            if family_changed:
                self.bot.latest_inventory = None

    def get_family_optimized(self, family_name, family):
        if family_name == "Eevee":
            return ([], [], [])

        candies = self.candies_by_family_name.get(family_name, 0)
        best_iv_pokemons = self.get_best_iv_in_family(family)
        best_relative_cp_pokemons = self.get_best_relative_cp_in_family(family)
        best_cp_pokemons = self.get_best_cp_in_family(family)

        best_pokemons = self.combine_pokemon_lists(best_iv_pokemons, best_relative_cp_pokemons)

        crap = family[:]
        crap = [p for p in crap if p not in best_pokemons]
        crap = [p for p in crap if p not in best_cp_pokemons]
        crap.sort(key=lambda p: p["iv"], reverse=True)

        evo_best_pokemons = []

        for pokemon in best_pokemons:
            next_amount = pokemon["next_amount"]

            if next_amount == 0:
                continue

            if next_amount <= candies:
                evo_best_pokemons.append(pokemon)
                candies -= next_amount

                next_name = pokemon["next_name"]

                if next_name:
                    next_family_data = self.family_data_by_pokemon_name[next_name]

                    if next_family_data["next_amount"] > 0:
                        # logging.info("Will try to multi evolve %s [IV %s] [CP %s]", pokemon["name"], pokemon["iv"], pokemon["cp"])

                        next_evo = dict(pokemon)
                        next_evo["name"] = next_name
                        next_evo.update(next_family_data)

                        best_pokemons.append(next_evo)
            else:
                break

        junior_next_amount = self.family_data_by_pokemon_name[family_name]["next_amount"]

        # leftover_candy = candies + transfer
        # transfer + keep_for_evo = len(crap)
        # keep_for_evo = int(leftover_candy / junior_next_amount)

        if junior_next_amount > 0:
            keep_for_evo = int((candies + len(crap)) / (junior_next_amount + 1))
        else:
            keep_for_evo = 0

        evo_crap_pokemons = [p for p in crap if p["next_amount"] == junior_next_amount][:keep_for_evo]
        transfer_pokemons = [p for p in crap if p not in evo_crap_pokemons]

        return (transfer_pokemons, evo_best_pokemons, evo_crap_pokemons)

    def apply_optimization(self, transfer_pokemons, evo_pokemons):
        family_changed = False

        for pokemon in transfer_pokemons:
            self.transfer_pokemon(pokemon)
            family_changed = True

        if self.use_lucky_egg:
            if (self.lucky_egg_count == 0) or (len(evo_pokemons) < 90):
                return family_changed

            self.do_use_lucky_egg()

        for pokemon in evo_pokemons:
            if self.evolve_pokemon(pokemon):
                family_changed = True
            else:
                break

        return family_changed

    def get_best_iv_in_family(self, family):
        best_pokemon = max(family, key=lambda p: p["iv"])
        return [p for p in family if p["iv"] == best_pokemon["iv"]]

    def get_best_relative_cp_in_family(self, family):
        best_pokemon = max(family, key=lambda p: p["relative_cp"])
        return [p for p in family if p["relative_cp"] == best_pokemon["relative_cp"]]

    def get_best_cp_in_family(self, family):
        best_pokemon = max(family, key=lambda p: p["cp"])
        return [p for p in family if p["cp"] == best_pokemon["cp"]]

    def transfer_pokemon(self, pokemon):
        if self.dry_run:
            pass
        else:
            self.bot.api.release_pokemon(pokemon_id=pokemon["id"])

        self.emit_event("pokemon_release",
                        formatted="Exchanged {pokemon} [IV {iv}] [CP {cp}]",
                        data={"pokemon": pokemon["name"],
                              "iv": pokemon["iv"],
                              "cp": pokemon["cp"]})

        if not self.dry_run:
            action_delay(self.bot.config.action_wait_min, self.bot.config.action_wait_max)

    def do_use_lucky_egg(self):
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
                            data={"amount_left": self.lucky_egg_count - 1})
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
            response_dict = self.bot.api.evolve_pokemon(pokemon_id=pokemon["id"])

        if not response_dict:
            return False

        result = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("result", 0)
        xp = response_dict.get("responses", {}).get("EVOLVE_POKEMON", {}).get("experience_awarded", 0)

        if result == 1:
            self.emit_event("pokemon_evolved",
                            formatted="Evolved {pokemon} [IV {iv}] [CP {cp}] [+{xp} xp]",
                            data={"pokemon": pokemon["name"],
                                  "iv": pokemon["iv"],
                                  "cp": pokemon["cp"],
                                  "xp": xp})

            if not self.dry_run:
                sleep(20)

            return True
        else:
            return False

    def refresh_inventory(self):
        self.family_by_family_name.clear()
        self.candies_by_family_name.clear()
        self.pokemon_count = 0

        inventory = self.bot.get_inventory()
        inventory_items = (inventory.get("responses", {})
                                    .get("GET_INVENTORY", {})
                                    .get("inventory_delta", {})
                                    .get("inventory_items", {}))

        for item in inventory_items:
            pokemon_data = item.get("inventory_item_data", {}).get("pokemon_data", {})
            candy_data = item.get("inventory_item_data", {}).get("candy", {})
            item_data = item.get("inventory_item_data", {}).get("item", {})

            if pokemon_data:
                self.pokemon_count += 1
                pokemon = self.get_pokemon_from_data(pokemon_data)

                if pokemon:
                    family_name = pokemon["family_name"]
                    self.family_by_family_name.setdefault(family_name, []).append(pokemon)
            elif candy_data:
                family_id = candy_data.get("family_id", 0)
                count = candy_data.get("candy", 0)

                if (family_id > 0) and (count > 0):
                    family_name = self.bot.pokemon_list[family_id - 1].get("Name")

                    if not family_name:
                        continue

                    self.candies_by_family_name[family_name] = count
            elif item_data:
                item_id = item_data.get("item_id", False)

                if item_id == Item.ITEM_LUCKY_EGG:
                    self.lucky_egg_count = item_data.get("count", 0)

    def get_pokemon_from_data(self, pokemon_data):
        pokemon_index = pokemon_data.get("pokemon_id", 0) - 1

        if pokemon_index < 0:
            return None

        pokemon_name = self.bot.pokemon_list[pokemon_index].get("Name")

        if not pokemon_name:
            logging.error("Invalid pokemon.json data file. Missing 'Name' field for pokemon_index '%s'", pokemon_index)
            return None

        family_data = self.family_data_by_pokemon_name.get(pokemon_name)

        if not family_data:
            logging.error("Invalid pokemon.json data file. Missing data for '%s'", pokemon_name)
            return None

        pokemon_cp = pokemon_data.get("cp", 0)
        pokemon_max_cp = self.get_pokemon_max_cp(pokemon_name)

        if pokemon_max_cp > 0:
            pokemon_relative_cp = float(pokemon_cp) / pokemon_max_cp
        else:
            pokemon_relative_cp = 0

        return {"id": pokemon_data.get("id", 0),
                "name": pokemon_name,
                "family_name": family_data["family_name"],
                "next_amount": family_data["next_amount"],
                "next_name": family_data["next_name"],
                "cp": pokemon_cp,
                "relative_cp": pokemon_relative_cp,
                "iv": self.get_pokemon_iv(pokemon_data)}

    def get_pokemon_iv(self, pokemon_data):
        iv = (pokemon_data.get("individual_attack", 0) +
              pokemon_data.get("individual_stamina", 0) +
              pokemon_data.get("individual_defense", 0))
        return round(iv / 45.0, 2)

    def get_pokemon_max_cp(self, pokemon_name):
        return int(self.pokemon_max_cp.get(pokemon_name, 0))

    def get_pokemon_max_cp_for_player(self, player_level, pokemon_name):
        return int(self.player_level_factor[player_level] * self.pokemon_max_cp.get(pokemon_name, 0))

    def combine_pokemon_lists(self, a, b):
        seen = set()
        return [p for p in a + b if not (p["id"] in seen or seen.add(p["id"]))]

    def init_player_level_factor(self):
        self.player_level_factor = [
            0, 0.094, 0.16639787, 0.21573247, 0.25572005, 0.29024988,
            0.3210876, 0.34921268, 0.37523559, 0.39956728, 0.4225,
            0.44310755, 0.46279839, 0.48168495, 0.49985844, 0.51739395,
            0.53435433, 0.55079269, 0.56675452, 0.58227891, 0.5974,
            0.61215729, 0.62656713, 0.64065295, 0.65443563, 0.667934,
            0.68116492, 0.69414365, 0.70688421, 0.71939909, 0.7317,
            0.73776948, 0.74378943, 0.74976104, 0.75568551, 0.76156384,
            0.76739717, 0.7731865, 0.77893275, 0.784637, 0.7903]

    def init_pokemon_max_cp(self):
        self.pokemon_max_cp = {
            "Abra": 600.44, "Aerodactyl": 2165.49, "Alakazam": 1813.82,
            "Arbok": 1767.13, "Arcanine": 2983.9, "Articuno": 2978.16,
            "Beedrill": 1439.96, "Bellsprout": 1117.43, "Blastoise": 2542.01,
            "Bulbasaur": 1071.54, "Butterfree": 1454.94, "Caterpie": 443.52,
            "Chansey": 675.12, "Charizard": 2602.2, "Charmander": 955.24,
            "Charmeleon": 1557.48, "Clefable": 2397.71, "Clefairy": 1200.96,
            "Cloyster": 2052.85, "Cubone": 1006.61, "Dewgong": 2145.77,
            "Diglett": 456.76, "Ditto": 919.62, "Dodrio": 1836.37,
            "Doduo": 855.41, "Dragonair": 1485.88, "Dragonite": 3500.06,
            "Dratini": 983.47, "Drowzee": 1075.14, "Dugtrio": 1168.55,
            "Eevee": 1077.2, "Ekans": 824.14, "Electabuzz": 2119.17,
            "Electrode": 1646.14, "Exeggcute": 1099.81, "Exeggutor": 2955.18,
            "Farfetch'd": 1263.89, "Fearow": 1746.35, "Flareon": 2643.43,
            "Gastly": 804.41, "Gengar": 2078.23, "Geodude": 849.49,
            "Gloom": 1689.46, "Golbat": 1921.35, "Goldeen": 965.14,
            "Golduck": 2386.52, "Golem": 2303.17, "Graveler": 1433.63,
            "Grimer": 1284.02, "Growlithe": 1335.03, "Gyarados": 2688.89,
            "Haunter": 1380.21, "Hitmonchan": 1516.51, "Hitmonlee": 1492.94,
            "Horsea": 764.67, "Hypno": 2184.16, "Ivysaur": 1632.19,
            "Jigglypuff": 917.64, "Jolteon": 2140.27, "Jynx": 1716.73,
            "Kabuto": 1104.72, "Kabutops": 2130.01, "Kadabra": 1131.96,
            "Kakuna": 485.35, "Kangaskhan": 2043.4, "Kingler": 1823.15,
            "Koffing": 1151.79, "Krabby": 792.21, "Lapras": 2980.73,
            "Lickitung": 1626.82, "Machamp": 2594.17, "Machoke": 1760.71,
            "Machop": 1089.59, "Magikarp": 262.7, "Magmar": 2265.3,
            "Magnemite": 890.68, "Magneton": 1879.95, "Mankey": 878.67,
            "Marowak": 1656.96, "Meowth": 756.32, "Metapod": 447.92,
            "Mew": 3299.17, "Mewtwo": 4144.75, "Moltres": 3240.47,
            "Mr. Mime": 1494.42, "Muk": 2602.9, "Nidoking": 2475.14,
            "Nidoqueen": 2485.03, "Nidoran F": 876.01, "Nidoran M": 843.14,
            "Nidorina": 1404.61, "Nidorino": 1372.5, "Ninetales": 2188.28,
            "Oddish": 1148.28, "Omanyte": 1119.77, "Omastar": 2233.65,
            "Onix": 857.2, "Paras": 916.6, "Parasect": 1747.07,
            "Persian": 1631.84, "Pidgeotto": 1223.98, "Pidgey": 679.93,
            "Pidgeot": 2091.39, "Pikachu": 887.69, "Pinsir": 2121.87,
            "Poliwag": 795.96, "Poliwhirl": 1340.43, "Poliwrath": 2505.33,
            "Ponyta": 1516.11, "Porygon": 1691.56, "Primeape": 1864.52,
            "Psyduck": 1109.56, "Raichu": 2028.3, "Rapidash": 2199.34,
            "Raticate": 1444.13, "Rattata": 581.65, "Rhydon": 2243.22,
            "Rhyhorn": 1182.08, "Sandshrew": 798.76, "Sandslash": 1810.22,
            "Scyther": 2073.96, "Seadra": 1713.22, "Seaking": 2043.92,
            "Seel": 1107.03, "Shellder": 822.91, "Slowbro": 2597.19,
            "Slowpoke": 1218.9, "Snorlax": 3112.85, "Spearow": 686.87,
            "Squirtle": 1008.69, "Starmie": 2182.14, "Staryu": 937.89,
            "Tangela": 1739.72, "Tauros": 1844.76, "Tentacool": 905.15,
            "Tentacruel": 2220.32, "Vaporeon": 2816.25, "Venomoth": 1890.32,
            "Venonat": 1029.39, "Venusaur": 2580.49, "Victreebel": 2530.52,
            "Vileplume": 2492.66, "Voltorb": 839.73, "Vulpix": 831.41,
            "Wartortle": 1582.79, "Weedle": 449.09, "Weepinbell": 1723.76,
            "Weezing": 2250.15, "Wigglytuff": 2177.2, "Zapdos": 3114.38,
            "Zubat": 642.51}

    def init_family_data_by_pokemon_name(self):
        for pokemon in self.bot.pokemon_list:
            pokemon_name = pokemon.get("Name")

            if not pokemon_name:
                logging.error("Invalid pokemon.json data file. Missing 'Name' field for '%s'", pokemon)
                continue

            prev_evo = pokemon.get("Previous evolution(s)")
            next_evo_req = pokemon.get("Next Evolution Requirements")
            next_evo = pokemon.get("Next evolution(s)")

            if next_evo and next_evo_req:
                next_amount = next_evo_req.get("Amount")
                next_name = next_evo[0].get("Name")

                if not next_amount:
                    logging.error("Invalid pokemon.json data file. Missing 'Amount' field for 'Next Evolution Requirements' of '%s'", pokemon_name)

                if not next_name:
                    logging.error("Invalid pokemon.json data file. Missing 'Name' field for 'Next Evolution Requirements' of '%s'", pokemon_name)
                else:
                    next_name = next_name.replace("candies", "").strip()
            else:
                next_amount = 0
                next_name = None

            if not prev_evo:
                self.family_data_by_pokemon_name[pokemon_name] = {"family_name": pokemon_name,
                                                                  "next_amount": next_amount,
                                                                  "next_name": next_name}
            else:
                family_name = prev_evo[0].get("Name")

                if family_name:
                    self.family_data_by_pokemon_name[pokemon_name] = {"family_name": family_name,
                                                                      "next_amount": next_amount,
                                                                      "next_name": next_name}
                else:
                    logging.error("Invalid pokemon.json data file. Missing 'Name' field for 'Previous evolution(s)' of '%s'", pokemon_name)
