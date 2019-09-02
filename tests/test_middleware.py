def test_append_text(master_channel, middleware):
    middleware.mode = "append_text"
    assert middleware.middleware_id in master_channel.send_text_msg().text


def test_interrupt(master_channel, middleware):
    middleware.mode = "interrupt"
    assert master_channel.send_text_msg() is None


def test_interrupt_non_text(master_channel, middleware):
    middleware.mode = "interrupt_non_text"
    assert master_channel.send_text_msg() is not None
    assert master_channel.send_link_msg() is None


def test_interrupt_status(master_channel, middleware):
    middleware.mode = "interrupt"
    assert master_channel.send_message_recall_status() is None


def test_get_extra_functions(middleware):
    extras = middleware.get_extra_functions()
    assert len(extras) == 1
    assert "echo" in extras
    assert extras['echo'] == middleware.echo
