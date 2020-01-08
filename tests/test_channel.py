def test_get_extra_functions(slave_channel):
    extras = slave_channel.get_extra_functions()
    assert len(extras) == 3
    assert "function_a" in extras
    assert extras['function_a'] == slave_channel.function_a
    assert "function_b" in extras
    assert extras['function_b'] == slave_channel.function_b
    assert "echo" in extras
    assert extras['echo'] == slave_channel.echo


def test_set_extra_function(slave_channel):
    assert len(slave_channel.function_a.name) > 0
    assert len(slave_channel.function_a.desc) > 0
    assert "{function_name}" in slave_channel.function_a.desc
