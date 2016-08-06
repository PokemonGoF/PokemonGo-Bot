from config import Config, get_config
import unittest


class ConfigSingletonTestCase(unittest.TestCase):

    def testConfigSingleton(self):
        class AttrHolder(object):
            pass

        obj = AttrHolder()
        obj.val = 1

        assert 0 == get_config('val', 0)

        config1 = Config()
        assert 0 == get_config('val', 0)

        config2 = Config()
        config2.initialize(obj)
        assert 1 == get_config('val', 0)

        obj.val = 2
        config1.initialize(obj)
        assert 2 == get_config('val', 0)

        config3 = Config()
        obj.val = 3
        assert 3 == get_config('val', 0)
