from config import Config, get_config
import unittest


class ConfigSingletonTestCase(unittest.TestCase):

    def testConfigSingleton(self):
        class AttrHolder(object):
            pass

        obj = AttrHolder()
        obj.val = 1
        obj.d = {'apple':'is delicious', 'banana':{'is':'good'}}

        assert 0 == get_config('val', 0)

        config1 = Config()
        assert 0 == get_config('val', 0) # not initialized yet.

        config2 = Config()
        config2.initialize(obj)
        assert 1 == get_config('val', 0) # initialized.

        obj.val = 2
        config1.initialize(obj)
        assert 2 == get_config('val', 0) # value changed, and other conf instance gets the canged value.

        config3 = Config()
        config3.config.val = 3 # value changed through an instance
        assert 3 == get_config('val', 0) # 

        assert 'is delicious' == get_config('d.apple', 'WRONG') # nested attribute test

        assert 'good' == get_config('d.banana.is', 'WRONG') # another nested attribute test
        
        assert 'WRONG' == get_config('d.pineapple.does.not.exist', 'WRONG') # some other nested attribute test

        assert 3 == config2.config.val # make sure direct access works as it used to

        assert 'good' == config2.config.d['banana']['is'] # same as above

