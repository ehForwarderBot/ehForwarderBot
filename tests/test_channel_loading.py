import unittest
import os
import shutil
import tempfile
import inspect

import yaml

import ehforwarderbot
import ehforwarderbot.__main__
import ehforwarderbot.utils
from ehforwarderbot import coordinator

from .mocks import master, slave, middleware


class ChannelLoadingTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_instance_id(self):
        with tempfile.TemporaryDirectory() as f:
            os.environ['EFB_DATA_PATH'] = f
            config_path = ehforwarderbot.utils.get_config_path()

            master_id = "tests.mocks.master.MockMasterChannel#instance1"
            slave_ids = [
                "tests.mocks.slave.MockSlaveChannel#instance1",
                "tests.mocks.slave.MockSlaveChannel#instance2"
            ]

            config = yaml.dump({
                "master_channel": master_id,
                "slave_channels": slave_ids
            })

            if not os.path.exists(os.path.dirname(config_path)):
                os.makedirs(os.path.dirname(config_path))
            with open(config_path, 'w') as conf_file:
                conf_file.write(config)
            ehforwarderbot.__main__.init()

            self.assertEqual(coordinator.master.channel_id, master_id)
            self.assertIsInstance(coordinator.master, master.MockMasterChannel)
            for i in slave_ids:
                self.assertIn(i, coordinator.slaves)
                self.assertIsInstance(coordinator.slaves[i], slave.MockSlaveChannel)

    def test_custom_path_module_loading(self):
        with tempfile.TemporaryDirectory() as f:
            os.environ['EFB_DATA_PATH'] = f
            config_path = ehforwarderbot.utils.get_config_path()
            modules_path = ehforwarderbot.utils.get_custom_modules_path()
            config = yaml.dump({
                "master_channel": "master.MockMasterChannel",
                "slave_channels": ["slave.MockSlaveChannel"],
                "middlewares": ["middleware.MockMiddleware"]
            })
            if not os.path.exists(os.path.dirname(config_path)):
                os.makedirs(os.path.dirname(config_path))
            if not os.path.exists(os.path.dirname(modules_path)):
                os.makedirs(os.path.dirname(modules_path))
            test_path = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), 'mocks')
            shutil.copy(os.path.join(test_path, 'master.py'), modules_path)
            shutil.copy(os.path.join(test_path, 'slave.py'), modules_path)
            shutil.copy(os.path.join(test_path, 'middleware.py'), modules_path)
            with open(config_path, 'w') as conf_file:
                conf_file.write(config)
            ehforwarderbot.__main__.init()

            self.assertEqual(coordinator.master.channel_id, master.MockMasterChannel.channel_id)
            self.assertIn(slave.MockSlaveChannel.channel_id, coordinator.slaves)
            self.assertEqual(coordinator.middlewares[0].middleware_id, middleware.MockMiddleware.middleware_id)

    def test_non_existing_module_loading(self):
        with tempfile.TemporaryDirectory() as f:
            os.environ['EFB_DATA_PATH'] = f
            config_path = ehforwarderbot.utils.get_config_path()
            config = yaml.dump({
                "master_channel": "nowhere_to_find.ThisChannel",
                "slave_channels": ["this_doesnt_exist.EitherChannel"]
            })
            if not os.path.exists(os.path.dirname(config_path)):
                os.makedirs(os.path.dirname(config_path))
            with open(config_path, 'w') as conf_file:
                conf_file.write(config)
            with self.assertRaises(ValueError):
                ehforwarderbot.__main__.init()

    def test_no_config_file(self):
        with tempfile.TemporaryDirectory() as f:
            os.environ['EFB_DATA_PATH'] = f
            with self.assertRaises(FileNotFoundError):
                ehforwarderbot.__main__.init()


if __name__ == '__main__':
    unittest.main()
