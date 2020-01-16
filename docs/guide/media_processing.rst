Media processing
================

Choosing media formats
----------------------

Both Master and Slave channel can take their charges
to convert media files they send or receive. In general:
**if a media file received from remote server is not a
common format, convert it before deliver it on; if a
media file sent to remote server requires to be in a
specific format, it should be converted before sending
out**. Nevertheless, this is only a guideline on
channels' responsibility regarding media processing,
and everyone has their own opinion on what is a common
format / encoding. Therefore we only recommend this
behaviour, but do not force in our code. This is to
say that, you still have to take care of the accepted
type of media encoding of your corresponding method of
presentation, and convert and/or fallback to different
type of representation if necessary. After all, the
delivery of information is more important.

Media encoders
--------------

Similarly, we will also not put a strict limit on this
as well, but just a recommendation. As you might have
already know, there are few mature pure Python media
processing libraries, most of them will more or less
requires internal or external binary dependencies.

We try to aim to use as few different libraries as we
can, as more library to install means more space,
install time, and complexity. While processing media
files, we recommend to use the following libraries
if possible:

- Pillow_
- FFmpeg_

.. _Pillow: https://pillow.readthedocs.io/en/stable/
.. _FFmpeg: shttps://www.ffmpeg.org/

Files in messages
-----------------

When a file sent out from a channel, it MUST be open,
and sought back to 0 ( ``file.seek(0)`` ) before sending.

Files sent MUST be able to be located somewhere in
the file system, and SHOULD with a appropriate extension
name, but not required. All files MUST also have its
MIME type specified in the message object. If the channel
is not sure about the correct MIME type, it can try to
guess with ``libmagic``, or fallback to ``application/octet-stream``.
Always try the best to provide the most suitable MIME
type when sending.

For such files, we use ``close`` to signify the end of its
lifecycle. If the file is not required by the sender's
channel anymore, it can be safely discarded.

Generally, ``tempfile.NamedTemporaryFile`` should work
for ordinary cases.
