import os
import pickle
import unittest

from mock import MagicMock, patch
from pokemongo_bot.cell_workers.spin_fort import SpinFort
from pokemongo_bot.inventory import Items

config = {
  "spin_wait_min": 0,
  "spin_wait_max": 0,
  "daily_spin_limit": 100,
}

response_dict = {'responses':
    {'FORT_SEARCH': {
        'experience_awarded': 50,
        'items_awarded': [
            {'item_id': 1, 'item_count': 1},
            {'item_id': 1, 'item_count': 1},
            {'item_id': 1, 'item_count': 1}
        ],
        'result': 1,
        'cooldown_complete_timestamp_ms': 1474592183629L,
        'chain_hack_sequence_number': 1}
    },
    'status_code': 1,
    'platform_returns': [
        {'type': 6, 'response': 'CAE='}
    ],
    'request_id': 4916374460149268503L
}

items_awarded = {u'Pokeball': 4}
egg_awarded = None
experience_awarded = 50

class SpinFortTestCase(unittest.TestCase):
    def setUp(self):
        self.patcherPokemonGoBot = patch('pokemongo_bot.PokemonGoBot')
        self.bot = self.patcherPokemonGoBot.start()

        forts_path = os.path.join(os.path.dirname(__file__),
            'resources', 'example_forts.pickle')
        with open(forts_path, 'rb') as forts:
           ex_forts = pickle.load(forts)

        self.patcherFortRange = patch('pokemongo_bot.cell_workers.spin_fort.SpinFort.get_forts_in_range')
        self.fort_range = self.patcherFortRange.start()
        self.fort_range.return_value = ex_forts

        self.patcherInventoryItem = patch('pokemongo_bot.inventory.Items')
        self.inventory_item = self.patcherInventoryItem.start()

    def tearDown(self):
        self.patcherPokemonGoBot.stop()
        self.patcherFortRange.stop()
        self.patcherInventoryItem.stop()

#    @patch('pokemongo_bot.cell_workers.spin_fort.SpinFort.get_items_awarded_from_fort_spinned')
#    def test_spin_fort(self, items_awarded):
#        spin_fort = SpinFort(self.bot, config)
#        self.bot.api = MagicMock()
#        self.bot.api.fort_search.return_value = response_dict
#        items_awarded.return_value = items_awarded

#        result = spin_fort.work()
#    self.assertEqual(result, 1)
