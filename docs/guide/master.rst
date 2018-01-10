Master channels
===============

Master channels are the interface that directly
or indirectly interact with the user. Despite the
first master channel of EFB (EFB Telegram Master)
is written in a form of Telegram Bot, master channels
can be written in many forms, such as:

* A web app
* A server that expose APIs to dedicated desktop and
  mobile clients
* A chat bot on an existing IM
* A server that compiles with a generic IM Protocol
* A CLI client
* Anything else you can think of...

Design guideline
----------------

When the master channel is implemented on an existing
protocol or platform, as far as possible, while
considering the user experience, a master channel should:

* maintain one thread / timeline per chat, indicating


.. figure:: ../_static/master-channel-0.png
    :align: center

    An example of an ideal design of a master channel,
    inspired by Telegram Desktop

