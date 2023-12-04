import random

def Singleton(cls):
    _instance = {}
 
    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]
 
    return _singleton


@Singleton
class OpenAI_ApiKeyManager():
    def __init__(self, mode='blacklist') -> None:
        # self.key_avail_list = []
        self.key_black_list = []
    
    def add_key_to_blacklist(self, key):
        self.key_black_list.append(key)

    def select_avail_key(self, key_list):
        if available_keys := [
            key for key in key_list if key not in self.key_black_list
        ]:
            return random.choice(available_keys)
        else:
            raise KeyError("No available key found.")