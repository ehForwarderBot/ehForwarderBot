import os

import pytest
from ruamel.yaml import YAML

import ehforwarderbot
import ehforwarderbot.config
import ehforwarderbot.utils
import ehforwarderbot.__main__
from ehforwarderbot import coordinator

from .mocks.master import MockMasterChannel
from .mocks.slave import MockSlaveChannel
from .mocks.middleware import MockMiddleware


yaml = YAML()


@pytest.fixture(scope="module")
def coord(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("efb_test")
    os.environ['EFB_DATA_PATH'] = str(tmp_path)
    config_path = ehforwarderbot.utils.get_config_path()
    config = {
        "master_channel": "tests.mocks.master.MockMasterChannel",
        "slave_channels": ["tests.mocks.slave.MockSlaveChannel"],
        "middlewares": ["tests.mocks.middleware.MockMiddleware"]
    }
    with config_path.open('w') as f:
        yaml.dump(config, f)
    config = ehforwarderbot.config.load_config()
    ehforwarderbot.__main__.init(config)
    assert coordinator.master.channel_id == MockMasterChannel.channel_id
    assert MockSlaveChannel.channel_id in coordinator.slaves
    assert coordinator.middlewares[0].middleware_id == MockMiddleware.middleware_id

    yield coordinator

    coordinator.master = None
    coordinator.slaves = {}
    coordinator.middlewares = []
    coordinator.master_thread = None
    coordinator.slave_threads = {}


@pytest.fixture(scope="module")
def master_channel(coord):
    return coord.master


@pytest.fixture(scope="module")
def slave_channel(coord):
    return coord.slaves[MockSlaveChannel.channel_id]


@pytest.fixture(scope="module")
def middleware(coord):
    return coord.middlewares[0]
