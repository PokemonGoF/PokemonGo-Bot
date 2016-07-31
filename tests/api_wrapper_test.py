import unittest
from mock import MagicMock, patch
from timeout_decorator import timeout, TimeoutError

from tests import FakeApi

from pgoapi import PGoApi
from pgoapi.exceptions import NotLoggedInException, ServerBusyOrOfflineException
from pokemongo_bot.api_wrapper import ApiWrapper

class TestApiWrapper(unittest.TestCase):
    def test_raises_not_logged_in_exception(self):
        api = ApiWrapper(PGoApi())
        api.get_inventory(test='awesome')
        with self.assertRaises(NotLoggedInException):
            api.call()

    def test_api_call_with_no_requests_set(self):
        api = ApiWrapper(PGoApi())
        with self.assertRaises(RuntimeError):
            api.call()

    @patch('pokemongo_bot.api_wrapper.sleep')
    def test_api_server_is_unreachable_raises_server_busy_or_offline_exception(self, sleep):
        sleep.return_value = True # we don't need to really sleep
        api = FakeApi('Wrong Value')
        api.get_inventory(test='awesome')
        # we expect an exception because the "server" isn't returning a valid response
        with self.assertRaises(ServerBusyOrOfflineException):
            api.call()

    def test_mocked_call(self):
        api = FakeApi(True)
        api._is_response_valid = MagicMock(return_value=True)
        api.get_inventory(test='awesome')
        result = api.call()
        self.assertTrue(result)

    def test_return_value_is_not_valid(self):

        def returnApi(ret_value):
            api = FakeApi(ret_value)
            api.get_inventory(test='awesome')
            return api

        wrong_return_values = [
            None,
            False,
            {},
            {'responses': {}},
            {'status_code': 0},
            {'responses': {'GET_INVENTORY_OR_NOT': {}}, 'status_code': 0}
        ]
        for wrong in wrong_return_values:
            api = returnApi(wrong)
            request_callers = api._pop_request_callers() # we can pop because we do no call

            is_valid = api._is_response_valid(wrong, request_callers)
            self.assertFalse(is_valid, 'return value {} is valid somehow ?'.format(wrong))

    def test_return_value_is_valid(self):
        api = FakeApi() # we set the return value below
        api.get_inventory(test='awesome')

        request = api.request_callers[0] # only one request
        self.assertEqual(request.upper(), 'GET_INVENTORY')

        good_return_value = {'responses': {request.upper(): {}}, 'status_code': 0}
        api.setApiReturnValue(good_return_value)

        result = api.call()
        self.assertEqual(result, good_return_value)
        self.assertEqual(len(api.request_callers), 0, 'request_callers must be empty')

    def test_multiple_requests(self):
        api = FakeApi()
        api.get_inventory(test='awesome')
        api.fort_details()

        good_return_value = {'responses': {'GET_INVENTORY': {}, 'FORT_DETAILS': {}}, 'status_code': 0}
        api.setApiReturnValue(good_return_value)

        result = api.call()
        self.assertEqual(result, good_return_value)

    @timeout(1)
    def test_api_call_throttle_should_pass(self):
        api = FakeApi(True)
        api._is_response_valid = MagicMock(return_value=True)
        api.requests_per_seconds = 5

        for i in range(api.requests_per_seconds):
            api.call()

    @timeout(1) # expects a timeout
    def test_api_call_throttle_should_fail(self):
        api = FakeApi(True)
        api._is_response_valid = MagicMock(return_value=True)
        api.requests_per_seconds = 5

        with self.assertRaises(TimeoutError):
            for i in range(api.requests_per_seconds * 2):
                api.call()
