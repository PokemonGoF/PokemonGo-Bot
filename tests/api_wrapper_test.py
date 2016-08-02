import unittest
from mock import MagicMock, patch
from timeout_decorator import timeout, TimeoutError

from tests import FakeApi

from pgoapi import PGoApi
from pgoapi.exceptions import NotLoggedInException, ServerBusyOrOfflineException, NoPlayerPositionSetException, EmptySubrequestChainException
from pokemongo_bot.api_wrapper import ApiWrapper

class TestApiWrapper(unittest.TestCase):
    def test_raises_not_logged_in_exception(self):
        api = ApiWrapper()
        api.set_position(*(42, 42, 0))
        request = api.create_request()
        request.get_inventory(test='awesome')
        with self.assertRaises(NotLoggedInException):
            request.call()

    def test_api_call_with_no_requests_set(self):
        request = ApiWrapper().create_request()
        with self.assertRaises(EmptySubrequestChainException):
            request.call()

    def test_api_wrong_request(self):
        request = ApiWrapper().create_request()
        with self.assertRaises(AttributeError):
            request.wrong_request()

    def test_raises_no_player_position_set_exception(self):
        request = ApiWrapper().create_request()
        request.get_inventory(test='awesome')
        with self.assertRaises(NoPlayerPositionSetException):
            request.call()

    @patch('pokemongo_bot.api_wrapper.sleep')
    def test_api_server_is_unreachable_raises_server_busy_or_offline_exception(self, sleep):
        sleep.return_value = True # we don't need to really sleep
        request = FakeApi().create_request('Wrong Value')
        request.get_inventory()
        # we expect an exception because the "server" isn't returning a valid response
        with self.assertRaises(ServerBusyOrOfflineException):
            request.call()

    def test_mocked_call(self):
        request = FakeApi().create_request(True)
        request.is_response_valid = MagicMock(return_value=True)
        request.get_inventory(test='awesome')
        result = request.call()
        self.assertTrue(result)

    def test_return_value_is_not_valid(self):
        api = FakeApi()
        def returnRequest(ret_value):
            request = api.create_request(ret_value)
            request.get_inventory(test='awesome')
            return request

        wrong_return_values = [
            None,
            False,
            {},
            {'responses': {}},
            {'status_code': 0},
            {'responses': {'GET_INVENTORY_OR_NOT': {}}, 'status_code': 0}
        ]
        for wrong in wrong_return_values:
            request = returnRequest(wrong)
            request_callers = request._pop_request_callers() # we can pop because we do no call

            is_valid = request.is_response_valid(wrong, request_callers)
            self.assertFalse(is_valid, 'return value {} is valid somehow ?'.format(wrong))

    def test_return_value_is_valid(self):
        request = FakeApi().create_request() # we set the return value below
        request.get_inventory(test='awesome')

        request_caller = request.request_callers[0] # only one request
        self.assertEqual(request_caller.upper(), 'GET_INVENTORY')

        good_return_value = {'responses': {request_caller.upper(): {}}, 'status_code': 0}
        request._call.return_value = good_return_value

        result = request.call()
        self.assertEqual(result, good_return_value)
        self.assertEqual(len(request.request_callers), 0, 'request_callers must be empty')

    def test_multiple_requests(self):
        request = FakeApi().create_request()
        request.get_inventory(test='awesome')
        request.fort_details()

        good_return_value = {'responses': {'GET_INVENTORY': {}, 'FORT_DETAILS': {}}, 'status_code': 0}
        request._call.return_value = good_return_value

        result = request.call()
        self.assertEqual(result, good_return_value)

    @timeout(1)
    def test_api_call_throttle_should_pass(self):
        request = FakeApi().create_request()
        request.is_response_valid = MagicMock(return_value=True)
        request.requests_per_seconds = 5

        for i in range(request.requests_per_seconds):
            request.call()

    @timeout(1) # expects a timeout
    def test_api_call_throttle_should_fail(self):
        request = FakeApi().create_request()
        request.is_response_valid = MagicMock(return_value=True)
        request.requests_per_seconds = 5

        with self.assertRaises(TimeoutError):
            for i in range(request.requests_per_seconds * 2):
                request.call()

    @patch('pokemongo_bot.api_wrapper.ApiRequest.is_response_valid')
    def test_api_direct_call(self, mock_method):
        mock_method.return_value = True

        result = FakeApi().get_inventory()
        self.assertEqual(result, 'mock return')
