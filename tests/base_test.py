import tempfile
import unittest
import os

from ruamel.yaml import YAML

import ehforwarderbot
import ehforwarderbot.config
import ehforwarderbot.utils
import ehforwarderbot.__main__
from ehforwarderbot import coordinator

from .mocks import master, slave, middleware


class StandardChannelTest(unittest.TestCase):
    def setUp(self):
        self.yaml = YAML()

        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ['EFB_DATA_PATH'] = self.temp_dir.name
        config_path = ehforwarderbot.utils.get_config_path()
        config = {
            "master_channel": "tests.mocks.master.MockMasterChannel",
            "slave_channels": ["tests.mocks.slave.MockSlaveChannel"],
            "middlewares": ["tests.mocks.middleware.MockMiddleware"]
        }
        if not os.path.exists(os.path.dirname(config_path)):
            os.makedirs(os.path.dirname(config_path))
        with open(config_path, 'w') as f:
            self.yaml.dump(config, f)
        config = ehforwarderbot.config.load_config()
        ehforwarderbot.__main__.init(config)
        self.assertEqual(coordinator.master.channel_id, master.MockMasterChannel.channel_id)
        self.assertIn(slave.MockSlaveChannel.channel_id, coordinator.slaves)
        self.assertEqual(coordinator.middlewares[0].middleware_id, middleware.MockMiddleware.middleware_id)

    def tearDown(self):
        self.temp_dir.cleanup()
