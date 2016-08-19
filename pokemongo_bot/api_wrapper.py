import time
import logging

from pgoapi.exceptions import (ServerSideRequestThrottlingException,
    NotLoggedInException, ServerBusyOrOfflineException,
    NoPlayerPositionSetException, EmptySubrequestChainException,
    UnexpectedResponseException)
from pgoapi.pgoapi import PGoApi, PGoApiRequest, RpcApi
from pgoapi.protos.POGOProtos.Networking.Requests.RequestType_pb2 import RequestType
from pgoapi.protos.POGOProtos.Networking.Envelopes.Signature_pb2 import Signature

from human_behaviour import sleep

class PermaBannedException(Exception):
    pass

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
        # Need fill in the location_fix
        location_fix = Signature.LocationFix()

        sensor_info = Signature.SensorInfo(
            timestamp_snapshot=20111,
            magnetometer_x=-0.04073212668299675,
            magnetometer_y=0.02653736248612404,
            magnetometer_z=-0.10395454615354538,
            angle_normalized_x=26.402721405029297,
            angle_normalized_y=-35.71720886230469,
            angle_normalized_z=-29.149093627929688,
            accel_raw_x=0.43482502851815374,
            accel_raw_y=0.8037761094798027,
            accel_raw_z=0.08975112865596838,
            gyroscope_raw_x=0.5030811429023743,
            gyroscope_raw_y=0.33783626556396484,
            gyroscope_raw_z=-0.2886628210544586,
            accel_normalized_x=0.08128999173641205,
            accel_normalized_y=-0.42125171422958374,
            accel_normalized_z=-0.9032933712005615,
            accelerometer_axes=3
        )
        device_info = Signature.DeviceInfo(
            device_id='HASHVALUE',
            device_brand='Apple',
            device_model='iPhone',
            device_model_boot='iPhone8,2',
            hardware_manufacturer='Apple',
            hardware_model='N66AP',
            firmware_brand='iPhone OS',
            firmware_type='9.3.3'
        )
        activity_status = Signature.ActivityStatus(
            walking=True,
            stationary=True,
            automotive=True,
            tilting=True
        )
        signature = Signature(
            #location_fix=location_fix,
            sensor_info=sensor_info,
            device_info=device_info,
            activity_status=activity_status
        )
        return PGoApiRequest.call(self, signature)

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

        try:
            # Permaban symptom is empty response to GET_INVENTORY and status_code = 3
            if result['status_code'] == 3 and 'GET_INVENTORY' in request_callers and not result['responses']['GET_INVENTORY']:
                raise PermaBannedException
        except KeyError:
            # Still wrong
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
