from mock import Mock, MagicMock, patch
from nose.tools import ok_, eq_, raises, timed, TimeExpired

from pgoapi import PGoApi
from pgoapi.exceptions import NotLoggedInException, ServerBusyOrOfflineException
from pokemongo_bot.api_wrapper import ApiWrapper

class TestApiWrapper(object):
    def setup(self):
        self._api = PGoApi()
        self.api = ApiWrapper(self._api)
        self.api.requests_per_seconds = 5

    def teardown(self):
        pass

    @raises(NotLoggedInException)
    def test_raises_not_logged_in_exception(self):
        self.api.get_inventory(test='awesome')
        self.api.call()

    @raises(RuntimeError)
    def test_api_call_with_no_requests_set(self):
        self.api.call()

    @raises(ServerBusyOrOfflineException)
    @patch('pokemongo_bot.api_wrapper.sleep')
    def test_api_server_is_unreachable_raises_server_busy_or_offline_exception(self, sleep):
        sleep.return_value = True # we don't need to really sleep
        self._api.call = MagicMock(return_value=True)
        self.api._can_call = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')
        self.api.call()

    def test_mocked_call(self):
        self._api.call = MagicMock(return_value=True)
        self.api._can_call = MagicMock(return_value=True)
        self.api._is_response_valid = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')
        result = self.api.call()
        ok_(result)

    def test_return_value_is_not_valid(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')

        wrong_return_values = [
            None,
            False,
            {},
            {'responses': {}},
            {'status_code': 0},
            {'responses': {'GET_INVENTORY_OR_NOT': {}}, 'status_code': 0}
        ]
        request_callers = self.api.request_callers
        for wrong in wrong_return_values:
            # self._api.call = MagicMock(return_value=wrong)

            is_valid = self.api._is_response_valid(wrong, request_callers)
            ok_(is_valid == False, 'return value {} is valid somehow ?'.format(wrong))


    def test_return_value_is_valid(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')

        good_return_value = {'responses': {'GET_INVENTORY': {}}, 'status_code': 0}
        self._api.call = MagicMock(return_value=good_return_value)

        result = self.api.call()
        eq_(result, good_return_value)
        ok_(len(self.api.request_callers) == 0, 'request_callers must be empty')

    def test_multiple_requests(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')
        self.api.fort_details()

        good_return_value = {'responses': {'GET_INVENTORY': {}, 'FORT_DETAILS': {}}, 'status_code': 0}
        self._api.call = MagicMock(return_value=good_return_value)

        result = self.api.call()
        eq_(result, good_return_value)

    @timed(1)
    def test_api_call_throttle_should_pass(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api._is_response_valid = MagicMock(return_value=True)

        for i in range(self.api.requests_per_seconds):
            self.api.call()

    @raises(TimeExpired)
    @timed(1)
    def test_api_call_throttle_should_fail(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api._is_response_valid = MagicMock(return_value=True)

        for i in range(self.api.requests_per_seconds * 2):
            self.api.call()
