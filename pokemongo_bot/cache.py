import logger
import time

class CacheObject(object):
    
    def __init__(self, response_type, data):
        self.response_type = response_type
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
        for response_type in responses:
            Cache.set(response_type, responses[response_type])
    
    @staticmethod
    def get(response_type):
        return Cache.database[response_type]
        
    @staticmethod
    def set(response_type, data):
        Cache.database[response_type] = CacheObject(response_type, data)
        
    @staticmethod
    def remove(response_type):
        del Cache.database[response_type]
        
    @staticmethod
    def clear():
        Cache.database = {}
    
    def clean(max_age=60):
        db = Cache.database
        for response_type in db:
            cache_object = db[response_type]
            
    @staticmethod
    def list_response_types():
        return Cache.database.keys()
    
    @staticmethod
    def print_ages():
        db = Cache.database
        for response_type in db:
            cache_object = db[response_type]
            logger.log("[CACHE] {} - {}".format(response_type, cache_object.age()), 'yellow')
            
    