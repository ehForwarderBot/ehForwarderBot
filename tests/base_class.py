import os

import pytest
from ruamel.yaml import YAML

import ehforwarderbot
import ehforwarderbot.config
import ehforwarderbot.utils
import ehforwarderbot.__main__
from ehforwarderbot import coordinator

from .mocks import master, slave, middleware


yaml = YAML()


@pytest.fixture(autouse=True)
def setup(tmp_path):
    temp_dir = tmp_path
    os.environ['EFB_DATA_PATH'] = str(temp_dir)
    config_path = ehforwarderbot.utils.get_config_path()
    config = {
        "master_channel": "tests.mocks.master.MockMasterChannel",
        "slave_channels": ["tests.mocks.slave.MockSlaveChannel"],
        "middlewares": ["tests.mocks.middleware.MockMiddleware"]
    }
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    config = ehforwarderbot.config.load_config()
    ehforwarderbot.__main__.init(config)
    assert coordinator.master.channel_id == master.MockMasterChannel.channel_id
    assert slave.MockSlaveChannel.channel_id in coordinator.slaves
    assert coordinator.middlewares[0].middleware_id == middleware.MockMiddleware.middleware_id

