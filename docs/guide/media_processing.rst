Media Processing
================

Both Master and Slave channel can take their charges
to convert media files they send or receive. In general:
**if a media file received from remote server is not a
common format, convert it before deliver it on; if a
media file sent to remote server requires to be in a
specific format, it should be converted before sending
out**. Nevertheless, this is only a guideline on
channels' responsibility regarding media processing —
we recommend this behaviour, but do not force in
code. This is to say that, you still have to take care
of the accepted type of media encoding of your
corresponding method of presentation, and convert and/or
fallback to different type of representation if necessary.
After all, the delivery of information is the first
priority.

.. TODO: List common media encodings.