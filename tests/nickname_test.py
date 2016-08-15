import unittest

from pokemongo_bot.cell_workers import NicknamePokemon
from pokemongo_bot.inventory import Pokemon


class NicknamePokemonTest(unittest.TestCase):
    def test_nickname_generation(self):
        # basic
        self.assertNicks('', ['', ''])
        self.assertNicks('{pokemon}', ['', ''])
        self.assertNicks('{name}', ['', ''])
        self.assertNicks('{Name}', ['', ''])
        self.assertNicks('{id}', ['42', '19'])
        self.assertNicks('{cp}', ['653', '106'])
        self.assertNicks('{CP}', ['653', '106'])
        self.assertNicks('{iv_attack}', ['9', '6'])
        self.assertNicks('{iv_defense}', ['4', '14'])
        self.assertNicks('{iv_stamina}', ['8', '0'])
        self.assertNicks('{iv_ads}', ['9/4/8', '6/14/0'])
        self.assertNicks('{iv_ads_hex}', ['948', '6E0'])
        self.assertNicks('{iv_sum}', ['21', '20'])
        self.assertNicks('{iv_pct}', ['047', '044'])
        self.assertNicks('{iv_pct2}', ['46', '44'])
        self.assertNicks('{iv_pct1}', ['4', '4'])
        self.assertNicks('{base_attack}', ['164', '92'])
        self.assertNicks('{base_defense}', ['164', '86'])
        self.assertNicks('{base_stamina}', ['150', '60'])
        self.assertNicks('{base_ads}', ['164/164/150', '92/86/60'])
        self.assertNicks('{attack}', ['173', '98'])
        self.assertNicks('{defense}', ['168', '100'])
        self.assertNicks('{stamina}', ['158', '60'])
        self.assertNicks('{sum_ads}', ['173/168/158', '98/100/60'])
        self.assertNicks('{ivcp_pct}', ['049', '038'])
        self.assertNicks('{ivcp_pct2}', ['48', '38'])
        self.assertNicks('{ivcp_pct1}', ['4', '3'])
        self.assertNicks('{fast_attack_char}', ['L', 'n'])
        self.assertNicks('{charged_attack_char}', ['h', 'n'])
        self.assertNicks('{attack_code}', ['Lh', 'nn'])
        self.assertNicks('{attack_pct}', ['047', '084'])
        self.assertNicks('{attack_pct2}', ['47', '83'])
        self.assertNicks('{attack_pct1}', ['4', '8'])
        self.assertNicks('{defense_pct}', ['082', '060'])
        self.assertNicks('{defense_pct2}', ['81', '60'])
        self.assertNicks('{defense_pct1}', ['7', '5'])

        # complex
        self.assertNicks('{name:2}', ['', ''])
        self.assertNicks('{pokemon.iv:.2%}', ['47.00%', '44.00%'])
        self.assertNicks('{pokemon.fast_attack}', ['Wing Attack', 'Tackle'])
        self.assertNicks('{pokemon.charged_attack}', ['Ominous Wind', 'Hyper Fang'])
        self.assertNicks('{pokemon.fast_attack.type}', ['Flying', 'Normal'])
        self.assertNicks('{pokemon.fast_attack.dps:.2f}', ['12.00', '10.91'])
        self.assertNicks('{pokemon.fast_attack.dps:.0f}', ['12', '11'])
        self.assertNicks('{iv_pct}_{iv_ads}', ['047_9/4/8', '044_6/14/0'])
        self.assertNicks('{iv_pct}_{iv_ads_hex}', ['047_948', '044_6E0'])
        self.assertNicks(
            '{ivcp_pct2}_{iv_pct2}_{iv_ads}',
            ['48_46_9/4/8', '38_44_6/14/0'])
        self.assertNicks(
            '{ivcp_pct2}_{iv_pct2}_{iv_ads_hex}',
            ['48_46_948', '38_44_6E0'])
        self.assertNicks(
            '{attack_code}{attack_pct1}{defense_pct1}{ivcp_pct1}{name}',
            ['Lh474Golbat', 'nn853Rattata'])

    #
    def setUp(self):
        self.bot = {}
        self.config = {}
        self.task = NicknamePokemon(self.bot, self.config)
        self.assertIs(self.task.bot, self.bot)
        self.assertIs(self.task.config, self.config)

        self.pokemons = [
            Pokemon({
                "num_upgrades": 2, "move_1": 210, "move_2": 69, "pokeball": 2,
                "favorite": 1, "pokemon_id": 42, "battles_attacked": 4,
                "stamina": 76, "stamina_max": 76, "individual_attack": 9,
                "individual_defense": 4, "individual_stamina": 8,
                "cp_multiplier": 0.4627983868122101,
                "additional_cp_multiplier": 0.018886566162109375,
                "cp": 653, "nickname": "Golb", "id": 13632861873471324}),
            Pokemon({
                "move_1": 221, "move_2": 129, "pokemon_id": 19, "cp": 106,
                "individual_attack": 6, "stamina_max": 22, "individual_defense": 14,
                "cp_multiplier": 0.37523558735847473, "id": 7841053399}),
        ]

    def assertNicks(self, template, expected_results):
        real_results = [self.task._generate_new_nickname(p, template)
                        for p in self.pokemons]
        self.assertListEqual(list(expected_results), real_results)

        # helper for test generation
        # print "self.assertNicks('{}', {})".format(template, real_results)
