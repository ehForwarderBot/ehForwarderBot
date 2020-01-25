Lifecycle
=========

This section talks about the lifecycle of an EFB instance, and that of a message
/ status.

Lifecycle of an EFB instance
----------------------------

The diagram below outlines the lifecycle of an EFB instance, and how channels
and middlewares are involved in it.

.. uml::
    :align: center
    :caption: Lifecycle of an EFB instance

    @startuml
    start
    :User starts an EFB instance;
    :Load profile configuration;
    :Import modules enabled;
    note right
        Modules are imported in the order specified in the
        profile config, master channels first, then slave
        channels and middlewares.
    end note
    :Initialize slave channels;
    note right
        Slave channels are initialized in the order specified
        in the profile config.

        When this is finished, the slave channel SHOULD be
        ready to response to all requests via method calls
        (""get_chats()"", ""get_chat_picture()"", etc).

        Messages from slave channels should be held until
        ""poll()"" is called.

        Note that master channel is **not** ready at this
        moment, interactions with the user through the
        framework is not possible. Master channel-specific
        interactions is possible by inspecting configs, but
        NOT RECOMMENDED, and SHOULD be avoided if an
        alternative solution is available.
    end note
    :Initialize master channel;
    note right
        Master channel can load data from slave channels
        enabled at this time, but not from middlewares.

        Messages from master channel should be held until
        ""poll()"" is called.
    end note
    :Initialize middlewares;
    note right
        Middlewares are initialized in the order specified
        in the profile config. At this moment, all channels
        are initialized and available.

        This is useful when a middleware would have
        channel-specific behaviors or would monkey-patch
        code in channels.
    end note
    :Poll master channel
    and slave channels;
    note right
        ""poll()"" of each channel is called in a separate
        Python thread. Messages SHOULD be sent between
        channels **only after** this method is called.
    end note
    :User triggers termination|
    :Call ""stop_polling()""
    of the master channel,
    and then slave channels;
    note right
        When ""stop_polling()"" is called, the channel
        SHOULD proceed with all clean-up procedures to
        prepare for its termination.

        When clean-up is finished, code running in the
        ""poll"" threads MUST be stopped to allow a
        graceful exit.
    end note
    :Join all ""poll"" threads;
    note right
        The framework will wait for all ""poll"" threads to
        finish their works for a graceful exit.
    end note
    stop
    @enduml

Lifecycle of a message
----------------------

The diagram below outlines the lifecycle of a message sending from a channel,
going through all middlewares, sent to the destination channel, and returned
back to the sending channel.

.. uml::
    :align: center
    :caption: Lifecycle of a message

    @startuml
    start
    :Message object is built and sent
    to the coordinator via ""coordinator.send_message()"";
    while (//for// each middleware) is (do)
        :Middleware processes
        and modify the message;
        if (Is message ""None""?) then (yes)
            :Return ""None"" to the sender;
            stop
        endif
    end while (finish)
    if (Is message valid?) then (yes)
    else (no)
        :Throw exception to sender;
        end
    endif
    :Deliver message to destination channel;
    :Return final message to the sender;
    note right
        Final message SHOULD contain the updated
        message ID if sent to a slave channel.
    end note
    stop
    @enduml

Status objects processed in the same way.
