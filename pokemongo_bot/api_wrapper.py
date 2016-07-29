# api_wrapper.py

from pgoapi import PGoApi
from pgoapi.exceptions import NotLoggedInException, ServerBusyOrOfflineException
from human_behaviour import sleep
import time
import logger

class ApiWrapper(object):
    def __init__(self, api):
        self._api = api
        self.request_callers = []
        self.reset_auth()
        self.last_api_request_time = None
        self.requests_per_seconds = 2

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

    def _pop_request_callers(self):
        r = self.request_callers
        self.request_callers = []
        return [i.upper() for i in r]

    def _is_response_valid(self, result, request_callers):
        if not result or result is None or not isinstance(result, dict):
            return False

        if not 'responses' in result or not 'status_code' in result:
            return False

        if not isinstance(result['responses'], dict):
            return False

        # the response can still programatically be valid at this point
        # but still be wrong. we need to check if the server did sent what we asked it
        for request_caller in request_callers:
            if not request_caller in result['responses']:
                return False

        return True


    def call(self, max_retry=5):
        request_callers = self._pop_request_callers()
        if not self._can_call():
            return False # currently this is never ran, exceptions are raised before

        request_timestamp = None

        api_req_method_list = self._api._req_method_list
        result = None
        try_cnt = 0
        while True:
            request_timestamp = self.throttle_sleep()
            self._api._req_method_list = [req_method for req_method in api_req_method_list] # api internally clear this field after a call
            result = self._api.call()
            if not self._is_response_valid(result, request_callers):
                try_cnt += 1
                logger.log('Server seems to be busy or offline - try again - {}/{}'.format(try_cnt, max_retry), 'red')

                if try_cnt >= max_retry:
                    raise ServerBusyOrOfflineException()
                sleep(1)
            else:
                break

        self.last_api_request_time = request_timestamp
        return result

    def login(self, provider, username, password):
        return self._api.login(provider, username, password)

    # fallback
    def __getattr__(self, func):
        DEFAULT_ATTRS = ['_position_lat', '_position_lng', '_auth_provider', '_api_endpoint', 'set_position', 'get_position']
        if func not in DEFAULT_ATTRS:
            self.request_callers.append(func)
        return getattr(self._api, func)

    def throttle_sleep(self):
        now_milliseconds = time.time() * 1000
        required_delay_between_requests = 1000 / self.requests_per_seconds

        difference = now_milliseconds - (self.last_api_request_time if self.last_api_request_time else 0)

        if (self.last_api_request_time != None and difference < required_delay_between_requests):
            sleep_time = required_delay_between_requests - difference
            time.sleep(sleep_time / 1000)

        return now_milliseconds
