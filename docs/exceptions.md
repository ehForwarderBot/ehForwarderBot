# Exceptions

Some standard exceptions that should be raised and caught in appropriate occasions.

## `EFBChatNotFound`
Raised by a slave channel when the recipient channel is not found when a message is sent.

## `EFBMessageTypeNotSupported`
Raised when an incoming message is in a type not supported by the recipient channel. Applicable to both master and slave channels.

## `EFBMessageNotFound`
Raised when a message is trying to "direct reply" to another message which couldn't be found. 
