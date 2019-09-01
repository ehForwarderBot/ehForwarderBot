import os
import shutil
import tempfile
import inspect
from pathlib import Path

import pytest
from ruamel.yaml import YAML

import ehforwarderbot
import ehforwarderbot.__main__
import ehforwarderbot.utils
import ehforwarderbot.config
from ehforwarderbot import coordinator

from .mocks import master, slave, middleware

yaml = YAML()


def test_instance_id():
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
        config = dump_and_load_config(config)
        ehforwarderbot.__main__.init(config)

        assert coordinator.master.channel_id == master_id
        assert isinstance(coordinator.master, master.MockMasterChannel)
        for i in slave_ids:
            assert i in coordinator.slaves
            assert isinstance(coordinator.slaves[i], slave.MockSlaveChannel)


def dump_and_load_config(config):
    config_path = ehforwarderbot.utils.get_config_path()
    with config_path.open('w') as f:
        yaml.dump(config, f)
    return ehforwarderbot.config.load_config()


def test_load_config():
    data = {
        "master_channel": "tests.mocks.master.MockMasterChannel",
        "slave_channels": ["tests.mocks.slave.MockSlaveChannel"],
        "middlewares": ["tests.mocks.middleware.MockMiddleware"]
    }
    config_path = ehforwarderbot.utils.get_config_path()
    with config_path.open('w') as f:
        yaml.dump(data, f)
    result = ehforwarderbot.config.load_config()
    for k, v in data.items():
        assert result[k] == v


def test_custom_path_module_loading():
    with tempfile.TemporaryDirectory() as f:
        os.environ['EFB_DATA_PATH'] = f
        modules_path = ehforwarderbot.utils.get_custom_modules_path()
        config = {
            "master_channel": "master.MockMasterChannel",
            "slave_channels": ["slave.MockSlaveChannel",
                               "slave.MockSlaveChannel#instance"],
            "middlewares": ["middleware.MockMiddleware",
                            "middleware.MockMiddleware#instance"]
        }
        test_path: Path = Path(inspect.getfile(inspect.currentframe())).parent / 'mocks'
        # noinspection PyTypeChecker
        shutil.copy(test_path / 'master.py', modules_path)
        # noinspection PyTypeChecker
        shutil.copy(test_path / 'slave.py', modules_path)
        # noinspection PyTypeChecker
        shutil.copy(test_path / 'middleware.py', modules_path)
        config = dump_and_load_config(config)
        ehforwarderbot.__main__.init(config)

        assert coordinator.master.channel_id == master.MockMasterChannel.channel_id
        assert coordinator.master.instance_id is None
        slave_0 = slave.MockSlaveChannel.channel_id
        assert slave_0 in coordinator.slaves
        assert coordinator.slaves[slave_0].instance_id is None
        slave_1 = slave_0 + "#instance"
        assert slave_1 in coordinator.slaves
        assert coordinator.slaves[slave_1].instance_id == "instance"
        assert coordinator.middlewares[0].middleware_id == middleware.MockMiddleware.middleware_id
        assert coordinator.middlewares[0].instance_id is None
        assert coordinator.middlewares[1].middleware_id == middleware.MockMiddleware.middleware_id + "#instance"
        assert coordinator.middlewares[1].instance_id == "instance"


def test_non_existing_module_loading():
    with tempfile.TemporaryDirectory() as f:
        os.environ['EFB_DATA_PATH'] = f
        config = {
            "master_channel": "nowhere_to_find.ThisChannel",
            "slave_channels": ["this_doesnt_exist.EitherChannel"]
        }
        with pytest.raises(ValueError):
            dump_and_load_config(config)


def test_no_config_file():
    with tempfile.TemporaryDirectory() as f:
        os.environ['EFB_DATA_PATH'] = f
        with pytest.raises(FileNotFoundError):
            ehforwarderbot.config.load_config()
