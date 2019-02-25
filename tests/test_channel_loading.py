import unittest
import os
import shutil
import tempfile
import inspect
from pathlib import Path

from ruamel.yaml import YAML

import ehforwarderbot
import ehforwarderbot.__main__
import ehforwarderbot.utils
import ehforwarderbot.config
from ehforwarderbot import coordinator

from .mocks import master, slave, middleware


class ChannelLoadingTest(unittest.TestCase):
    def setUp(self):
        self.yaml = YAML()

    def test_instance_id(self):
        with tempfile.TemporaryDirectory() as f:
            os.environ['EFB_DATA_PATH'] = f

            master_id = "tests.mocks.master.MockMasterChannel#instance1"
            slave_ids = [
                "tests.mocks.slave.MockSlaveChannel#instance1",
                "tests.mocks.slave.MockSlaveChannel#instance2"
            ]

            config = {
                "master_channel": master_id,
                "slave_channels": slave_ids
            }
            config = self.dump_and_load_config(config)
            ehforwarderbot.__main__.init(config)

            self.assertEqual(coordinator.master.channel_id, master_id)
            self.assertIsInstance(coordinator.master, master.MockMasterChannel)
            for i in slave_ids:
                self.assertIn(i, coordinator.slaves)
                self.assertIsInstance(coordinator.slaves[i], slave.MockSlaveChannel)

    def dump_and_load_config(self, config):
        config_path = ehforwarderbot.utils.get_config_path()
        with open(config_path, 'w') as f:
            self.yaml.dump(config, f)
        return ehforwarderbot.config.load_config()

    def test_load_config(self):
        data = {
            "master_channel": "tests.mocks.master.MockMasterChannel",
            "slave_channels": ["tests.mocks.slave.MockSlaveChannel"],
            "middlewares": ["tests.mocks.middleware.MockMiddleware"]
        }
        config_path = ehforwarderbot.utils.get_config_path()
        with open(config_path, 'w') as f:
            self.yaml.dump(data, f)
        result = ehforwarderbot.config.load_config()
        for k, v in data.items():
            assert result[k] == v

    def test_custom_path_module_loading(self):
        with tempfile.TemporaryDirectory() as f:
            os.environ['EFB_DATA_PATH'] = f
            modules_path = ehforwarderbot.utils.get_custom_modules_path()
            config = {
                "master_channel": "master.MockMasterChannel",
                "slave_channels": ["slave.MockSlaveChannel"],
                "middlewares": ["middleware.MockMiddleware"]
            }
            test_path = Path(inspect.getfile(inspect.currentframe())).parent / 'mocks'
            # noinspection PyTypeChecker
            shutil.copy(test_path / 'master.py', modules_path)
            # noinspection PyTypeChecker
            shutil.copy(test_path / 'slave.py', modules_path)
            # noinspection PyTypeChecker
            shutil.copy(test_path / 'middleware.py', modules_path)
            config = self.dump_and_load_config(config)
            ehforwarderbot.__main__.init(config)

            self.assertEqual(coordinator.master.channel_id, master.MockMasterChannel.channel_id)
            self.assertIn(slave.MockSlaveChannel.channel_id, coordinator.slaves)
            self.assertEqual(coordinator.middlewares[0].middleware_id, middleware.MockMiddleware.middleware_id)

    def test_non_existing_module_loading(self):
        with tempfile.TemporaryDirectory() as f:
            os.environ['EFB_DATA_PATH'] = f
            config = {
                "master_channel": "nowhere_to_find.ThisChannel",
                "slave_channels": ["this_doesnt_exist.EitherChannel"]
            }
            with self.assertRaises(ValueError):
                config = self.dump_and_load_config(config)
                ehforwarderbot.__main__.init(config)

    def test_no_config_file(self):
        with tempfile.TemporaryDirectory() as f:
            os.environ['EFB_DATA_PATH'] = f
            with self.assertRaises(FileNotFoundError):
                ehforwarderbot.config.load_config()


if __name__ == '__main__':
    unittest.main()
