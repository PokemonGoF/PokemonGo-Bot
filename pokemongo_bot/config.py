class Config(object):
    _instance = None
    config = None
    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    def __init__(self):
        pass

    @staticmethod
    def initialize(config):
        Config.config = config
          
    @staticmethod
    def __getattr__(name):
        if None != Config.config:
            return getattr(Config.config, name)
        return None


def _recursive_getattr(obj, attrNames):
    if 0 == len(attrNames):
        return obj
    else:
        if type(obj) == dict and attrNames[0] in obj:
            return _recursive_getattr(obj[attrNames[0]], attrNames[1:])
        else:
            return None


def get_config(attr, default):
    '''
    Utility for getting config value.
    Instead of writing

    if 'attr1' in Config.config.dic and 'attr2' in Config.config.dic['attr1']:
        value = Config.config.dic['attr1']['attr2']
    else:
        value = default

    you can simply write

    value = get_config('dic.attr1.attr2', default)

    Array indexing is not supported yet.
    TODO: Maybe add memoize???
          Be careful with changin the conf values in the case...

    '''
    attr_ar = attr.split('.')
    if None != Config.config and hasattr(Config.config, attr_ar[0]):
        obj = getattr(Config.config, attr_ar[0])
        if 1 == len(attr_ar):
            return obj
        else:
            ret = _recursive_getattr(obj, attr_ar[1:])
    else:
        ret = None

    if None == ret:
        # logger.log("Config for %s not found, using default = %s"%(attr, repr(default)))
        ret = default
    return ret

