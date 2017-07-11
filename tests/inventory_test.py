import unittest

from pokemongo_bot.inventory import *


class InventoryTest(unittest.TestCase):
    def test_types(self):
        td = Types
        self.assertIs(types_data(), td)
        self.assertEqual(len(td.STATIC_DATA), 18)
        self.assertEqual(len(td.all()), 18)

        for name, s in td.STATIC_DATA.iteritems():
            assert len(name) > 0
            self.assertIs(s.name, name)
            for t in s.attack_effective_against:
                self.assertIn(s, t.pokemon_vulnerable_to)
            for t in s.attack_weak_against:
                self.assertIn(s, t.pokemon_resistant_to)
            for t in s.pokemon_vulnerable_to:
                self.assertIn(s, t.attack_effective_against)
            for t in s.pokemon_resistant_to:
                self.assertIn(s, t.attack_weak_against)

    def test_pokemons(self):
        # Init data
        self.assertEqual(len(Pokemons().all()), 0)  # No inventory loaded here

        obj = Pokemons
        self.assertEqual(len(obj.STATIC_DATA), 251)

        for idx in xrange(len(obj.STATIC_DATA)):
            pokemon = obj.STATIC_DATA[idx]  # type: PokemonInfo
            name = pokemon.name
            pokemon_id = pokemon.id
            self.assertEqual(pokemon.id, idx+1)
            assert (1 <= pokemon_id <= 251)

            self.assertGreaterEqual(len(pokemon.movesets), 1)
            self.assertIsInstance(pokemon.movesets[0], Moveset)
            assert 200 <= pokemon.max_cp <= 4761
            assert 1 <= len(pokemon.types) <= 2
            assert 1 <= pokemon.base_attack <= 800
            assert 20 <= pokemon.base_defense <= 500
            assert 20 <= pokemon.base_stamina <= 800
            assert .0 <= pokemon.capture_rate <= .76
            assert .0 <= pokemon.flee_rate <= .99
            assert 1 <= len(pokemon._data['Weaknesses']) <= 7
            assert 3 <= len(name) <= 10

            self.assertGreaterEqual(len(pokemon.classification), 11)
            self.assertGreaterEqual(len(pokemon.fast_attacks), 1)
            self.assertGreaterEqual(len(pokemon.charged_attack), 1)

            self.assertIs(obj.data_for(pokemon_id), pokemon)
            self.assertIs(obj.name_for(pokemon_id), name)

            first_evolution_id = obj.first_evolution_id_for(pokemon_id)
            self.assertIs(first_evolution_id, pokemon.first_evolution_id)
            self.assertIs(pokemon.family_id, first_evolution_id)
            self.assertGreaterEqual(first_evolution_id, 1)
            next_evolution_ids = obj.next_evolution_ids_for(pokemon_id)
            self.assertIs(next_evolution_ids, pokemon.next_evolution_ids)
            last_evolution_ids = obj.last_evolution_ids_for(pokemon_id)
            self.assertIs(last_evolution_ids, pokemon.last_evolution_ids)
            candies_cost = obj.evolution_cost_for(pokemon_id)
            self.assertIs(candies_cost, pokemon.evolution_cost)
            self.assertIs(obj.prev_evolution_id_for(pokemon_id), pokemon.prev_evolution_id)
            self.assertGreaterEqual(len(last_evolution_ids), 1)

            if not obj.has_next_evolution(pokemon_id):
                assert not pokemon.has_next_evolution
                self.assertEqual(pokemon.evolution_cost, 0)
                self.assertEqual(pokemon.next_evolution_ids, [])
                self.assertEqual(pokemon.next_evolutions_all, [])
                self.assertEqual(pokemon.last_evolution_ids, [pokemon_id])
            else:
                self.assertGreater(candies_cost, 0)
                self.assertGreaterEqual(len(next_evolution_ids), 1)
                self.assertLessEqual(len(next_evolution_ids), len(last_evolution_ids))

                reqs = pokemon._data['Next Evolution Requirements']
                #self.assertEqual(reqs["Family"], first_evolution_id)
                candies_name = obj.name_for(first_evolution_id) + ' candies'
                #self.assertEqual(reqs["Name"], candies_name)
                assert 12 <= candies_cost <= 400
                self.assertEqual(reqs["Amount"], candies_cost)

                evolutions = pokemon._data["Next evolution(s)"]
                self.assertGreaterEqual(len(evolutions), len(next_evolution_ids))

                for p in evolutions:
                    p_id = int(p["Number"])
                    self.assertNotEqual(p_id, pokemon_id)
                    self.assertEqual(p["Name"], obj.name_for(p_id))

                for p_id in next_evolution_ids:
                    self.assertEqual(obj.prev_evolution_id_for(p_id), pokemon_id)
                    prev_evs = obj.data_for(p_id)._data["Previous evolution(s)"]
                    self.assertGreaterEqual(len(prev_evs), 1)
                    self.assertEqual(int(prev_evs[-1]["Number"]), pokemon_id)
                    self.assertEqual(prev_evs[-1]["Name"], name)

                # Only Eevee has 3 next evolutions
                #self.assertEqual(len(next_evolution_ids),
                #                 1 if pokemon_id != 133 else 3)

            if "Previous evolution(s)" in pokemon._data:
                for p in pokemon._data["Previous evolution(s)"]:
                    p_id = int(p["Number"])
                    self.assertNotEqual(p_id, pokemon_id)
                    self.assertEqual(p["Name"], obj.name_for(p_id))

        #
        # Specific pokemons testing

        poke = Pokemon({
            "num_upgrades": 2, "move_1": 210, "move_2": 69, "pokeball": 2,
            "favorite": 1, "pokemon_id": 42, "battles_attacked": 4,
            "stamina": 76, "stamina_max": 76, "individual_attack": 9,
            "individual_defense": 4, "individual_stamina": 8,
            "cp_multiplier": 0.4627983868122101,
            "additional_cp_multiplier": 0.018886566162109375,
            "cp": 653, "nickname": "Golb", "id": 13632861873471324,
            "pokemon_display": {"shiny": False }})
        self.assertEqual(poke.level, 13)
        self.assertEqual(poke.iv, 0.47)
        self.assertEqual(poke.shiny, False)
        self.assertAlmostEqual(poke.ivcp, 0.4857492694248581)
        self.assertAlmostEqual(poke.static.max_cp, 1830.17768446934)
        self.assertAlmostEqual(poke.cp_percent, 0.33943779314748107)
        self.assertEqual(poke.name, 'Golbat')
        self.assertEqual(poke.nickname, "Golb")
        self.assertEqual(poke.nickname_raw, poke.nickname)
        self.assertAlmostEqual(poke.moveset.dps,15.130190007037298 )
        self.assertAlmostEqual(poke.moveset.dps_attack, 16.256157635467982)
        self.assertAlmostEqual(poke.moveset.dps_defense, 6.377929397804805 )
        self.assertAlmostEqual(poke.moveset.attack_perfection, 0.1976822769744798)
        self.assertAlmostEqual(poke.moveset.defense_perfection, 0.62438387986335)

        poke = Pokemon({
            "move_1": 221, "move_2": 129, "pokemon_id": 19, "cp": 106,
            "individual_attack": 6, "stamina_max": 22, "individual_defense": 14,
            "cp_multiplier": 0.37523558735847473, "id": 7841053399,
            "pokemon_display": {"shiny": False }})
        self.assertEqual(poke.level, 8)
        self.assertEqual(poke.iv, 0.44)
        self.assertAlmostEqual(poke.ivcp, 0.38537234816542393)
        self.assertAlmostEqual(poke.static.max_cp, 588.4452706026287)
        self.assertAlmostEqual(poke.cp_percent, 0.1851585323747926)
        self.assertFalse(poke.is_favorite)
        self.assertEqual(poke.name, 'Rattata')
        self.assertEqual(poke.nickname, poke.name)
        self.assertEqual(poke.nickname_raw, '')
        self.assertAlmostEqual(poke.moveset.dps, 17.333333333333332 )
        self.assertAlmostEqual(poke.moveset.dps_attack, 21.666666666666668)
        self.assertAlmostEqual(poke.moveset.dps_defense, 4.814814814814815)
        self.assertAlmostEqual(poke.moveset.attack_perfection, 0.777011494252873)
        self.assertAlmostEqual(poke.moveset.defense_perfection, 0.08099928856783224)

    def test_levels_to_cpm(self):
        l2c = LevelToCPm
        self.assertIs(levels_to_cpm(), l2c)
        max_cpm = l2c.cp_multiplier_for(l2c.MAX_LEVEL)
        self.assertEqual(l2c.MAX_LEVEL, 40)
        self.assertEqual(l2c.MAX_CPM, max_cpm)
        self.assertEqual(len(l2c.STATIC_DATA), 79)

        self.assertEqual(l2c.cp_multiplier_for(1), 0.094)
        self.assertEqual(l2c.cp_multiplier_for(1.0), 0.094)
        self.assertEqual(l2c.cp_multiplier_for(17.5), 0.558830576)
        self.assertEqual(l2c.cp_multiplier_for(40.0), 0.79030001)
        self.assertEqual(l2c.cp_multiplier_for(40), 0.79030001)

        self.assertEqual(l2c.level_from_cpm(0.79030001), 40.0)
        self.assertEqual(l2c.level_from_cpm(0.7903), 40.0)

    def test_attacks(self):
        self._test_attacks(fast_attacks, FastAttacks)
        self._test_attacks(charged_attacks, ChargedAttacks)

    def _test_attacks(self, callback, clazz):
        charged = clazz is ChargedAttacks
        self.assertIs(callback(), clazz)

        # check consistency
        attacks = clazz.all_by_dps()
        number = len(attacks)
        assert (number > 0)
        self.assertGreaterEqual(len(clazz.BY_TYPE), 17)
        self.assertEqual(number, len(clazz.all()))
        self.assertEqual(number, len(clazz.STATIC_DATA))
        self.assertEqual(number, len(clazz.BY_NAME))
        self.assertEqual(number, sum([len(l) for l in clazz.BY_TYPE.values()]))

        # check data
        prev_dps = float("inf")
        for attack in attacks:  # type: Attack
            self.assertGreater(attack.id, 0)
            self.assertGreater(len(attack.name), 0)
            self.assertIsInstance(attack.type, Type)
            self.assertGreaterEqual(attack.damage, 0)
            self.assertGreater(attack.duration, .0)
            self.assertGreater(attack.energy, 0)
            self.assertGreaterEqual(attack.dps, 0)
            assert (.0 <= attack.rate_in_type <= 1.0)
            self.assertLessEqual(attack.dps, prev_dps)
            self.assertEqual(attack.is_charged, charged)
            self.assertIs(attack, clazz.data_for(attack.id))
            self.assertIs(attack, clazz.by_name(attack.name))
            assert (attack in clazz.list_for_type(attack.type))
            assert (attack in clazz.list_for_type(attack.type.name))
            self.assertIsInstance(attack, ChargedAttack if charged else Attack)
            prev_dps = attack.dps
