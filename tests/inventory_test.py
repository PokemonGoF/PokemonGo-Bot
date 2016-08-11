import unittest

from pokemongo_bot.inventory import *


class InventoryTest(unittest.TestCase):
    def test_pokemons(self):
        # Init data
        self.assertEqual(len(Pokemons().all()), 0)  # No inventory loaded here

        obj = Pokemons
        self.assertEqual(len(obj.STATIC_DATA), 151)

        for poke_info in obj.STATIC_DATA:
            name = poke_info['Name']
            pokemon_id = int(poke_info['Number'])
            self.assertTrue(1 <= pokemon_id <= 151)

            self.assertGreaterEqual(len(poke_info['movesets']), 1)
            self.assertTrue(262 <= poke_info['max_cp'] <= 4145)
            self.assertTrue(1 <= len(poke_info['types']) <= 2)
            self.assertTrue(40 <= poke_info['BaseAttack'] <= 284)
            self.assertTrue(54 <= poke_info['BaseDefense'] <= 242)
            self.assertTrue(20 <= poke_info['BaseStamina'] <= 500)
            self.assertTrue(.0 <= poke_info['CaptureRate'] <= .56)
            self.assertTrue(.0 <= poke_info['FleeRate'] <= .99)
            self.assertTrue(1 <= len(poke_info['Weaknesses']) <= 7)
            self.assertTrue(3 <= len(name) <= 10)

            self.assertGreaterEqual(len(poke_info['Classification']), 11)
            self.assertGreaterEqual(len(poke_info['Fast Attack(s)']), 1)
            self.assertGreaterEqual(len(poke_info['Special Attack(s)']), 1)

            self.assertIs(obj.data_for(pokemon_id), poke_info)
            self.assertIs(obj.name_for(pokemon_id), name)

            first_evolution_id = obj.first_evolution_id_for(pokemon_id)
            self.assertGreaterEqual(first_evolution_id, 1)
            next_evolution_ids = obj.next_evolution_ids_for(pokemon_id)
            last_evolution_ids = obj.last_evolution_ids_for(pokemon_id)
            candies_cost = obj.evolution_cost_for(pokemon_id)
            obj.prev_evolution_id_for(pokemon_id)  # just call test
            self.assertGreaterEqual(len(last_evolution_ids), 1)

            if not obj.has_next_evolution(pokemon_id):
                assert 'Next evolution(s)' not in poke_info
                assert 'Next Evolution Requirements' not in poke_info
            else:
                self.assertGreaterEqual(len(next_evolution_ids), 1)
                self.assertLessEqual(len(next_evolution_ids), len(last_evolution_ids))

                reqs = poke_info['Next Evolution Requirements']
                self.assertEqual(reqs["Family"], first_evolution_id)
                candies_name = obj.name_for(first_evolution_id) + ' candies'
                self.assertEqual(reqs["Name"], candies_name)
                self.assertIsNotNone(candies_cost)
                self.assertTrue(12 <= candies_cost <= 400)
                self.assertEqual(reqs["Amount"], candies_cost)

                evolutions = poke_info["Next evolution(s)"]
                self.assertGreaterEqual(len(evolutions), len(next_evolution_ids))

                for p in evolutions:
                    p_id = int(p["Number"])
                    self.assertNotEqual(p_id, pokemon_id)
                    self.assertEqual(p["Name"], obj.name_for(p_id))

                for p_id in next_evolution_ids:
                    self.assertEqual(obj.prev_evolution_id_for(p_id), pokemon_id)
                    prev_evs = obj.data_for(p_id)["Previous evolution(s)"]
                    self.assertGreaterEqual(len(prev_evs), 1)
                    self.assertEqual(int(prev_evs[-1]["Number"]), pokemon_id)
                    self.assertEqual(prev_evs[-1]["Name"], name)

                # Only Eevee has 3 next evolutions
                self.assertEqual(len(next_evolution_ids),
                                 1 if pokemon_id != 133 else 3)

            if "Previous evolution(s)" in poke_info:
                for p in poke_info["Previous evolution(s)"]:
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
            "cp": 653, "nickname": "Golb", "id": 13632861873471324})
        self.assertEqual(poke.level, 12.5)
        self.assertEqual(poke.iv, 0.47)
        self.assertAlmostEqual(poke.ivcp, 0.488747515)
        self.assertAlmostEqual(poke.max_cp, 1921.34561459)
        self.assertAlmostEqual(poke.cp_percent, 0.340368964)
        self.assertTrue(poke.is_favorite)
        self.assertEqual(poke.name, 'Golbat')
        self.assertEqual(poke.nickname, "Golb")
        self.assertAlmostEqual(poke.moveset.dps, 10.7540173053)
        self.assertAlmostEqual(poke.moveset.dps_attack, 12.14462299)
        self.assertAlmostEqual(poke.moveset.dps_defense, 4.876681614)
        self.assertAlmostEqual(poke.moveset.attack_perfection, 0.4720730048)
        self.assertAlmostEqual(poke.moveset.defense_perfection, 0.8158081497)

        poke = Pokemon({
            "move_1": 221, "move_2": 129, "pokemon_id": 19, "cp": 106,
            "individual_attack": 6, "stamina_max": 22, "individual_defense": 14,
            "cp_multiplier": 0.37523558735847473, "id": 7841053399})
        self.assertEqual(poke.level, 7.5)
        self.assertEqual(poke.iv, 0.44)
        self.assertAlmostEqual(poke.ivcp, 0.3804059)
        self.assertAlmostEqual(poke.max_cp, 581.64643575)
        self.assertAlmostEqual(poke.cp_percent, 0.183759867)
        self.assertFalse(poke.is_favorite)
        self.assertEqual(poke.name, 'Rattata')
        self.assertEqual(poke.nickname, 'Rattata')
        self.assertAlmostEqual(poke.moveset.dps, 12.5567813108)
        self.assertAlmostEqual(poke.moveset.dps_attack, 15.6959766385)
        self.assertAlmostEqual(poke.moveset.dps_defense, 5.54282440561)
        self.assertAlmostEqual(poke.moveset.attack_perfection, 0.835172881385)
        self.assertAlmostEqual(poke.moveset.defense_perfection, 0.603137650999)

    def test_levels_to_cpm(self):
        l2c = LevelToCPm
        self.assertIs(levels_to_cpm(), l2c)
        max_cpm = l2c.cp_multiplier_for(l2c.MAX_LEVEL)
        self.assertEqual(l2c.MAX_LEVEL, 40)
        self.assertEqual(l2c.MAX_CPM, max_cpm)
        self.assertEqual(len(l2c.STATIC_DATA), 79)

        self.assertEqual(l2c.cp_multiplier_for("1"), 0.094)
        self.assertEqual(l2c.cp_multiplier_for(1), 0.094)
        self.assertEqual(l2c.cp_multiplier_for(1.0), 0.094)
        self.assertEqual(l2c.cp_multiplier_for("17.5"), 0.558830576)
        self.assertEqual(l2c.cp_multiplier_for(17.5), 0.558830576)
        self.assertEqual(l2c.cp_multiplier_for('40.0'), 0.79030001)
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
        self.assertTrue(number > 0)
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
            self.assertGreater(len(attack.type), 0)
            self.assertGreaterEqual(attack.damage, 0)
            self.assertGreater(attack.duration, .0)
            self.assertGreater(attack.energy, 0)
            self.assertGreaterEqual(attack.dps, 0)
            self.assertTrue(.0 <= attack.rate_in_type <= 1.0)
            self.assertLessEqual(attack.dps, prev_dps)
            self.assertEqual(attack.is_charged, charged)
            self.assertIs(attack, clazz.data_for(attack.id))
            self.assertIs(attack, clazz.by_name(attack.name))
            self.assertTrue(attack in clazz.BY_TYPE[attack.type])
            self.assertIsInstance(attack, ChargedAttack if charged else Attack)
            prev_dps = attack.dps
