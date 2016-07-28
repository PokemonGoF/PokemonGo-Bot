# api_wrapper.py

from pgoapi import PGoApi
from pgoapi.exceptions import NotLoggedInException
from human_behaviour import sleep
import logger

class ApiWrapper(object):
    def __init__(self, api):
        self._api = api
        self.reset_auth()

    def reset_auth(self):
        self._api._auth_token = None
        self._api._auth_provider = None
        self._api._api_endpoint = None

    # wrap api methods
    def _can_call(self):
        if not self._api._req_method_list or len(self._api._req_method_list) == 0:
            raise RuntimeError('Trying to call the api without setting any request')
        if self._api._auth_provider is None or not self._api._auth_provider.is_login():
            logger.log('Not logged in!', 'red')
            raise NotLoggedInException()
        return True

    def call(self, max_retry=5):
        if not self._can_call():
            return False

        api_req_method_list = self._api._req_method_list
        result = None
        try_cnt = 0
        while True:
            self._api._req_method_list = [req_method for req_method in api_req_method_list] # api internally clear this field after a call
            result = self._api.call()
            if result is None:
                try_cnt += 1
                logger.log('Server seems to be busy or offline - try again - {}/{}'.format(try_cnt, max_retry), 'red')
                if try_cnt >= max_retry:
                    raise ServerBusyOrOfflineException()
                sleep(1)
            else:
                break
        return result

    def login(self, provider, username, password):
        return self._api.login(provider, username, password)

    # fallback
    def __getattr__(self, func):
        return getattr(self._api, func)



