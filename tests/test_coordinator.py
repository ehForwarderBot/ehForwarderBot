import pytest


def test_matching_keys(coord):
    assert coord.slaves.keys() == coord.slave_threads.keys()


def test_get_module_by_id(coord, master_channel, slave_channel, middleware):
    assert coord.get_module_by_id(master_channel.channel_id) is not None
    assert coord.get_module_by_id(slave_channel.channel_id) is not None
    assert coord.get_module_by_id(middleware.middleware_id) is not None
    with pytest.raises(NameError):
        coord.get_module_by_id("non_existing.module")
