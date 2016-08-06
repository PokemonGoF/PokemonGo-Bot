class Config(object):
    _instance = None
    _initialized = False
    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    def __init__(self):
        pass

    def initialize(self, config):
        self.config = config
        Config._initialized = True
            
    def __getattr__(self, name):
        if Config._initialized:
            if hasattr(self, 'config'):
                return getattr(self.config, name)
        return None

def get_config(attr, default, config=Config()):
    if Config._initialized and  hasattr(config, attr):
        ret = getattr(config, attr)
    else:
        # logger.log("Config for %s not found, using default = %s"%(attr, repr(default)))
        ret = default
    return ret

