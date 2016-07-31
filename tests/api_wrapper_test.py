import unittest
from mock import MagicMock, patch
from tests import TimeoutError, timeout, SKIP_TIMED

from pgoapi import PGoApi
from pgoapi.exceptions import NotLoggedInException, ServerBusyOrOfflineException
from pokemongo_bot.api_wrapper import ApiWrapper


class TestApiWrapper(unittest.TestCase):
    def setUp(self):
        self._api = PGoApi()
        self.api = ApiWrapper(self._api)
        self.api.requests_per_seconds = 5

    def tearDown(self):
        pass

    def test_raises_not_logged_in_exception(self):
        with self.assertRaises(NotLoggedInException):
            self.api.get_inventory(test='awesome')
            self.api.call()

    def test_api_call_with_no_requests_set(self):
        with self.assertRaises(RuntimeError):
            self.api.call()

    @patch('pokemongo_bot.api_wrapper.sleep')
    def test_api_server_is_unreachable_raises_server_busy_or_offline_exception(self, sleep):
        sleep.return_value = True # we don't need to really sleep
        self._api.call = MagicMock(return_value=True)
        self.api._can_call = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')
        with self.assertRaises(ServerBusyOrOfflineException):
            self.api.call()

    def test_mocked_call(self):
        self._api.call = MagicMock(return_value=True)
        self.api._can_call = MagicMock(return_value=True)
        self.api._is_response_valid = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')
        result = self.api.call()
        self.assertTrue(result)

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
            self.assertFalse(is_valid, 'return value {} is valid somehow ?'.format(wrong))

    def test_return_value_is_valid(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')

        request = self.api.request_callers[0] # only one request
        self.assertEqual(request.upper(), 'GET_INVENTORY')

        good_return_value = {'responses': {request.upper(): {}}, 'status_code': 0}
        self._api.call = MagicMock(return_value=good_return_value)

        result = self.api.call()
        self.assertEqual(result, good_return_value)
        self.assertEqual(len(self.api.request_callers), 0, 'request_callers must be empty')

    def test_multiple_requests(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api.get_inventory(test='awesome')
        self.api.fort_details()

        good_return_value = {'responses': {'GET_INVENTORY': {}, 'FORT_DETAILS': {}}, 'status_code': 0}
        self._api.call = MagicMock(return_value=good_return_value)

        result = self.api.call()
        self.assertEqual(result, good_return_value)

    @unittest.skipIf(SKIP_TIMED, "Please install module 'timeout_decorator'")
    @timeout(1)
    def test_api_call_throttle_should_pass(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api._is_response_valid = MagicMock(return_value=True)

        for i in range(self.api.requests_per_seconds):
            self.api.call()

    @unittest.skipIf(SKIP_TIMED, "Please install module 'timeout_decorator'")
    @timeout(1)
    def test_api_call_throttle_should_fail(self):
        self.api._can_call = MagicMock(return_value=True)
        self.api._is_response_valid = MagicMock(return_value=True)

        with self.assertRaises(TimeoutError):
            for i in range(self.api.requests_per_seconds * 2):
                self.api.call()
