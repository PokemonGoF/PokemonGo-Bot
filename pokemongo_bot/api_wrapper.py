import time
import logging
import random, base64, struct
import hashlib
import os
import json
from pgoapi.exceptions import (ServerSideRequestThrottlingException,
                               NotLoggedInException, ServerBusyOrOfflineException,
                               NoPlayerPositionSetException, EmptySubrequestChainException,
                               UnexpectedResponseException)
from pgoapi.pgoapi import PGoApi, PGoApiRequest, RpcApi
from pgoapi.protos.POGOProtos.Networking.Requests.RequestType_pb2 import RequestType
from pgoapi.protos.POGOProtos.Networking.Envelopes.Signature_pb2 import Signature
from pgoapi.utilities import get_time
from pokemongo_bot.datastore import Datastore
from human_behaviour import sleep, gps_noise_rng
from pokemongo_bot.base_dir import _base_dir

class PermaBannedException(Exception):
    pass


class ApiWrapper(Datastore, PGoApi):
    DEVICE_ID = None

    def __init__(self, config=None):
        PGoApi.__init__(self)
        # Set to default, just for CI...
        self.actual_lat, self.actual_lng, self.actual_alt = PGoApi.get_position(self)
        self.teleporting = False
        self.noised_lat, self.noised_lng, self.noised_alt = self.actual_lat, self.actual_lng, self.actual_alt

        self.useVanillaRequest = False
        self.config = config

        if self.config is None or self.config.username is None:
            ApiWrapper.DEVICE_ID = "3d65919ca1c2fc3a8e2bd7cc3f974c34"
            return
        file_salt = None
        did_path = os.path.join(_base_dir, 'data', 'deviceid-%s.txt' % self.config.username)
        if os.path.exists(did_path):
            file_salt = open(did_path, 'r').read()
        if self.config is not None:
            key_string = self.config.username
            if file_salt is not None:
                # Config and file are set, so use those.
                ApiWrapper.DEVICE_ID = hashlib.md5(key_string + file_salt).hexdigest()
            else:
                # Config is set, but file isn't, so make it.
                rand_float = random.SystemRandom().random()
                salt = base64.b64encode((struct.pack('!d', rand_float)))
                ApiWrapper.DEVICE_ID = hashlib.md5(key_string + salt).hexdigest()
                with open(did_path, "w") as text_file:
                    text_file.write("{0}".format(salt))
        else:
            if file_salt is not None:
                # No config, but there's a file, use it.
                ApiWrapper.DEVICE_ID = hashlib.md5(file_salt).hexdigest()
            else:
                # No config or file, so make up a reasonable default.
                ApiWrapper.DEVICE_ID = "3d65919ca1c2fc3a8e2bd7cc3f974c34"

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

    def set_position(self, lat, lng, alt=None, teleporting=False):
        self.actual_lat = lat
        self.actual_lng = lng
        if None != alt:
            self.actual_alt = alt
        else:
            alt = self.actual_alt
        self.teleporting = teleporting
        
        if self.config.replicate_gps_xy_noise:
            lat_noise = gps_noise_rng(self.config.gps_xy_noise_range)
            lng_noise = gps_noise_rng(self.config.gps_xy_noise_range)
            lat = lat + lat_noise
            lng = lng + lng_noise
        if self.config.replicate_gps_z_noise:
            alt_noise = gps_noise_rng(self.config.gps_z_noise_range)
            alt = alt + alt_noise

        self.noised_lat, self.noised_lng, self.noised_alt = lat, lng, alt

        PGoApi.set_position(self, lat, lng, alt)

    def get_position(self):
        return (self.actual_lat, self.actual_lng, self.actual_alt)


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
        location_fix = [Signature.LocationFix(
            provider='fused',
            timestamp_snapshot=(get_time(ms=True) - RpcApi.START_TIME) - random.randint(100, 300),
            latitude=self._position_lat,
            longitude=self._position_lng,
            horizontal_accuracy=round(random.uniform(50, 250), 7),
            altitude=self._position_alt,
            vertical_accuracy=random.randint(2, 5),
            provider_status=3,
            location_type=1
        )]

        sensor_info = Signature.SensorInfo(
            timestamp_snapshot=(get_time(ms=True) - RpcApi.START_TIME) - random.randint(200, 400),
            magnetometer_x=random.uniform(-0.139084026217, 0.138112977147),
            magnetometer_y=random.uniform(-0.2, 0.19),
            magnetometer_z=random.uniform(-0.2, 0.4),
            angle_normalized_x=random.uniform(-47.149471283, 61.8397789001),
            angle_normalized_y=random.uniform(-47.149471283, 61.8397789001),
            angle_normalized_z=random.uniform(-47.149471283, 5),
            accel_raw_x=random.uniform(0.0729667818829, 0.0729667818829),
            accel_raw_y=random.uniform(-2.788630499244109, 3.0586791383810468),
            accel_raw_z=random.uniform(-0.34825887123552773, 0.19347580173737935),
            gyroscope_raw_x=random.uniform(-0.9703824520111084, 0.8556089401245117),
            gyroscope_raw_y=random.uniform(-1.7470258474349976, 1.4218578338623047),
            gyroscope_raw_z=random.uniform(-0.9681901931762695, 0.8396636843681335),
            accel_normalized_x=random.uniform(-0.31110161542892456, 0.1681540310382843),
            accel_normalized_y=random.uniform(-0.6574847102165222, -0.07290205359458923),
            accel_normalized_z=random.uniform(-0.9943905472755432, -0.7463029026985168),
            accelerometer_axes=3
        )
        device_info = Signature.DeviceInfo(
            device_id=ApiWrapper.DEVICE_ID,
            device_brand='Apple',
            device_model='iPhone',
            device_model_boot='iPhone8,2',
            hardware_manufacturer='Apple',
            hardware_model='N66AP',
            firmware_brand='iPhone OS',
            firmware_type='9.3.3'
        )
        activity_status = Signature.ActivityStatus(
            # walking=True,
            # stationary=True,
            # automotive=True,
            # tilting=True
        )
        signature = Signature(
            location_fix=location_fix,
            sensor_info=sensor_info,
            device_info=device_info,
            activity_status=activity_status,
            unknown25=-8537042734809897855
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
            return False  # currently this is never ran, exceptions are raised before

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
                sleep(1)  # huge sleep ?
                continue  # skip response checking

            if should_unexpected_response_retry:
                unexpected_response_retry += 1
                if unexpected_response_retry >= 5:
                    self.logger.warning(
                        'Server is not responding correctly to our requests.  Waiting for 30 seconds to reconnect.')
                    sleep(30)
                else:
                    sleep(2)
                continue

            if not self.is_response_valid(result, request_callers):
                try_cnt += 1
                if try_cnt > 3:
                    self.logger.warning(
                        'Server seems to be busy or offline - try again - {}/{}'.format(try_cnt, max_retry))
                if try_cnt >= max_retry:
                    raise ServerBusyOrOfflineException()
                sleep(1)
            else:
                break

        self.last_api_request_time = request_timestamp
        return result

    def __getattr__(self, func):
        if func.upper() in RequestType.keys():
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
