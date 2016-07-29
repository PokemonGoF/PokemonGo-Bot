import logger
import time

class CacheObject(object):
    
    def __init__(self, name, data):
        self.name = name
        self.data = data
        self.time_stamp = int(time.time())
        
    def age(self):
        return int(time.time()) - self.time_stamp
        
    def is_outdated(self, max_age=60):
        return max_age <= self.age()
        
class Cache(object):
    
    database = {}
    
    @staticmethod
    def process_response(response):
        responses = response['responses']
        for type in responses:
            Cache.set(type, responses[type])
    
    @staticmethod
    def get(type):
        return Cache.database[type]
        
    @staticmethod
    def set(type, data):
        Cache.database[type] = CacheObject(type, data)
        
    @staticmethod
    def remove(type):
        del Cache.database[type]
        
    @staticmethod
    def clear():
        Cache.database = {}
        
    @staticmethod
    def print_ages():
        db = Cache.database
        for type in db:
            cache_object = db[type]
            logger.log("[CACHE] {} - {}".format(type, cache_object.age()), 'yellow')
            
    