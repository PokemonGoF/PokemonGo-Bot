import time
import logging

from pgoapi.exceptions import (ServerSideRequestThrottlingException,
    NotLoggedInException, ServerBusyOrOfflineException,
    NoPlayerPositionSetException, EmptySubrequestChainException,
    UnexpectedResponseException)
from pgoapi.pgoapi import PGoApi, PGoApiRequest, RpcApi
from pgoapi.protos.POGOProtos.Networking.Requests_pb2 import RequestType

from human_behaviour import sleep

class ApiWrapper(PGoApi):
    def __init__(self):
        PGoApi.__init__(self)
        self.useVanillaRequest = False

    def create_request(self):
        RequestClass = ApiRequest
        if self.useVanillaRequest:
            RequestClass = PGoApiRequest

        return RequestClass(
            self,
            self._position_lat,
            self._position_lng,
            self._position_alt
        )

    def login(self, *args):
        # login needs base class "create_request"
        self.useVanillaRequest = True
        try:
            ret_value = PGoApi.login(self, *args)
        finally:
            # cleanup code
            self.useVanillaRequest = False
        return ret_value


class ApiRequest(PGoApiRequest):
    def __init__(self, *args):
        PGoApiRequest.__init__(self, *args)
        self.logger = logging.getLogger(__name__)
        self.request_callers = []
        self.last_api_request_time = None
        self.requests_per_seconds = 2

    def can_call(self):
        if not self._req_method_list:
            raise EmptySubrequestChainException()

        if (self._position_lat is None) or (self._position_lng is None) or (self._position_alt is None):
            raise NoPlayerPositionSetException()

        if self._auth_provider is None or not self._auth_provider.is_login():
            self.log.info('Not logged in')
            raise NotLoggedInException()

        return True

    def _call(self):
        return PGoApiRequest.call(self)

    def _pop_request_callers(self):
        r = self.request_callers
        self.request_callers = []
        return [i.upper() for i in r]

    def is_response_valid(self, result, request_callers):
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

    def call(self, max_retry=15):
        request_callers = self._pop_request_callers()
        if not self.can_call():
            return False # currently this is never ran, exceptions are raised before

        request_timestamp = None
        api_req_method_list = self._req_method_list
        result = None
        try_cnt = 0
        throttling_retry = 0
        unexpected_response_retry = 0
        while True:
            request_timestamp = self.throttle_sleep()
            # self._call internally clear this field, so save it
            self._req_method_list = [req_method for req_method in api_req_method_list]
            should_throttle_retry = False
            should_unexpected_response_retry = False
            try:
                result = self._call()
            except ServerSideRequestThrottlingException:
                should_throttle_retry = True
            except UnexpectedResponseException:
                should_unexpected_response_retry = True

            if should_throttle_retry:
                throttling_retry += 1
                if throttling_retry >= max_retry:
                    raise ServerSideRequestThrottlingException('Server throttled too many times')
                sleep(1) # huge sleep ?
                continue # skip response checking

            if should_unexpected_response_retry:
                unexpected_response_retry += 1
                if unexpected_response_retry >= 5:
                    self.logger.warning('Server is not responding correctly to our requests.  Waiting for 30 seconds to reconnect.')
                    sleep(30)
                else:
                    sleep(2)
                continue

            if not self.is_response_valid(result, request_callers):
                try_cnt += 1
                if try_cnt > 3:
                    self.logger.warning('Server seems to be busy or offline - try again - {}/{}'.format(try_cnt, max_retry))
                if try_cnt >= max_retry:
                    raise ServerBusyOrOfflineException()
                sleep(1)
            else:
                break

        self.last_api_request_time = request_timestamp
        return result

    def __getattr__(self, func):
        if func.upper() in  RequestType.keys():
            self.request_callers.append(func)
        return PGoApiRequest.__getattr__(self, func)

    def throttle_sleep(self):
        now_milliseconds = time.time() * 1000
        required_delay_between_requests = 1000 / self.requests_per_seconds

        difference = now_milliseconds - (self.last_api_request_time if self.last_api_request_time else 0)

        if self.last_api_request_time != None and difference < required_delay_between_requests:
            sleep_time = required_delay_between_requests - difference
            time.sleep(sleep_time / 1000)

        return now_milliseconds
