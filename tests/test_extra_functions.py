import unittest

from .mocks.slave import MockSlaveChannel


class SlaveChannelExtraFunctionsTest(unittest.TestCase):
    def test_get_extra_functions_list(self):
        channel = MockSlaveChannel()
        self.assertIn('echo', channel.get_extra_functions())
        self.assertEqual(len(channel.get_extra_functions()), 1)
        echo = channel.get_extra_functions()['echo']
        self.assertTrue(callable(echo))
        self.assertTrue(hasattr(echo, 'name'))
        self.assertTrue(hasattr(echo, 'desc'))
        self.assertIn('{function_name}', echo.desc)
