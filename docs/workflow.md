# Walk-through — How EFB works

## `main.py`
`main.py` first defines a queue `q` for processing any message from slave channels to master channel.

Then, loads from `config.py`, it gets a list of activated slave channels and master channel. Channels objects are init-ed one by one, with `q` as the parameter, and stored to a list named `slaves`. Right after that, object for master channel is also created.

At this point of time, all channels should be initialized and logged in (Additional actions may be requied for log in).