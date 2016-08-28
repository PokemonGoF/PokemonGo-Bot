import unittest
from mock import patch
from pokemongo_bot.cell_workers.incubate_eggs import IncubateEggs


class IncubateEggsTestCase(unittest.TestCase):

    @patch('pokemongo_bot.PokemonGoBot')
    def testFilterAndSort_AllowNone(self, mock_pokemongo_bot):
        incubate_eggs = IncubateEggs(mock_pokemongo_bot, {})

        incubate_eggs.eggs = [{"km": 2.0}, {"km": 5.0}, {"km": 5.0}]

        allowed = []
        sorting = True

        result = incubate_eggs._filter_sort_eggs(allowed, sorting)
        self.assertEqual([], result)


    @patch('pokemongo_bot.PokemonGoBot')
    def testFilterAndSort_AllowSome(self, mock_pokemongo_bot):
        incubate_eggs = IncubateEggs(mock_pokemongo_bot, {})

        incubate_eggs.eggs = [{"km": 5.0}, {"km": 2.0}, {"km": 5.0}, {"km": 10.0}]

        allowed = [2, 10]
        sorting = True

        result = incubate_eggs._filter_sort_eggs(allowed, sorting)
        self.assertEqual([{"km": 10.0}, {"km": 2.0}], result)


    @patch('pokemongo_bot.PokemonGoBot')
    def testFilterAndSort_AllowSomeNoReverseSort(self, mock_pokemongo_bot):
        incubate_eggs = IncubateEggs(mock_pokemongo_bot, {})

        incubate_eggs.eggs = [{"km": 5.0}, {"km": 2.0}, {"km": 5.0}, {"km": 10.0}]

        allowed = [2, 10]
        sorting = False

        result = incubate_eggs._filter_sort_eggs(allowed, sorting)
        self.assertEqual([{"km": 2.0}, {"km": 10.0}], result)



    @patch('pokemongo_bot.PokemonGoBot')
    def testFilterAndSort_AllowAll(self, mock_pokemongo_bot):
        incubate_eggs = IncubateEggs(mock_pokemongo_bot, {})

        incubate_eggs.eggs = [{"km": 5.0}, {"km": 2.0}, {"km": 5.0}]

        allowed = [2, 5, 10]
        sorting = True

        result = incubate_eggs._filter_sort_eggs(allowed, sorting)
        self.assertEqual([{"km": 5.0}, {"km": 5.0}, {"km": 2.0}], result)
