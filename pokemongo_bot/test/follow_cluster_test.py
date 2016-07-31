import unittest, pickle, os
from mock import patch
from pokemongo_bot.cell_workers.follow_cluster import FollowCluster


class FollowClusterTestCase(unittest.TestCase):

    @patch('pokemongo_bot.PokemonGoBot')
    def testWorkAway(self, mock_pokemongo_bot):
        forts_path = os.path.join(os.path.dirname(__file__), 'resources', 'example_forts.pickle')
        with open(forts_path, 'rb') as forts:
            ex_forts = pickle.load(forts)
        config = {'radius': 50, 'lured': False}
        mock_pokemongo_bot.position = (37.396787, -5.994587)
        mock_pokemongo_bot.config.walk = 4.16
        mock_pokemongo_bot.get_forts.return_value = ex_forts
        follow_cluster = FollowCluster(mock_pokemongo_bot, config)
        assert follow_cluster.work() == [37.39718375014263, -5.9932912500000013]
        assert follow_cluster.is_at_destination == False
        assert follow_cluster.announced == False

    @patch('pokemongo_bot.PokemonGoBot')
    def testWorkArrived(self, mock_pokemongo_bot):
        forts_path = os.path.join(os.path.dirname(__file__), 'resources', 'example_forts.pickle')
        with open(forts_path, 'rb') as forts:
            ex_forts = pickle.load(forts)
        config = {'radius': 50, 'lured': False}
        mock_pokemongo_bot.position = (37.39718375014263, -5.9932912500000013)
        mock_pokemongo_bot.config.walk = 4.16
        mock_pokemongo_bot.get_forts.return_value = ex_forts
        follow_cluster = FollowCluster(mock_pokemongo_bot, config)
        assert follow_cluster.work() == [37.39718375014263, -5.9932912500000013]
        assert follow_cluster.is_at_destination == True
        assert follow_cluster.announced == False
