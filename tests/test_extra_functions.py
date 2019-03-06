

from .mocks.slave import MockSlaveChannel


def test_get_extra_functions_list():
    channel = MockSlaveChannel()
    assert 'echo' in channel.get_extra_functions()
    assert len(channel.get_extra_functions()) == 1
    echo = channel.get_extra_functions()['echo']
    assert callable(echo)
    assert hasattr(echo, 'name')
    assert hasattr(echo, 'desc')
    assert '{function_name}' in echo.desc
