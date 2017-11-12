# coding=utf-8

import telegram
import telegram.ext
import telegram.error
import telegram.constants
import config
import datetime
import utils
import urllib
import html
import logging
import time
import magic
import os
import re
import mimetypes
import pydub
import threading
import traceback
import base64
from typing import Optional
from moviepy.editor import VideoFileClip
from ehforwarderbot.channel import EFBChannel, EFBMsg, MsgType, ChatType, TargetType, ChannelType
from ehforwarderbot.exceptions import EFBChatNotFound, EFBMessageTypeNotSupported, EFBMessageError
from . import db, speech
from .whitelisthandler import WhitelistHandler
from .msgType import get_msg_type, TGMsgType


class Flags:
    # General Flags
    CANCEL_PROCESS = "cancel"
    # Chat linking
    CONFIRM_LINK = 0x11
    EXEC_LINK = 0x12
    # Start a chat
    START_CHOOSE_CHAT = 0x21
    # Command
    COMMAND_PENDING = 0x31
    # Message recipient suggestions
    SUGGEST_RECIPIENT= 0x32


class TelegramChannel(EFBChannel):
    """
    EFB Channel - Telegram (Master)
    Requires python-telegram-bot

    Author: Eana Hufwe <https://github.com/blueset>

    External Services:
        You may need API keys from following service providers to enjoy more functions.
        Baidu Speech Recognition API: http://yuyin.baidu.com/
        Bing Speech API: https://www.microsoft.com/cognitive-services/en-us/speech-api

    Additional configs:
    eh_telegram_master = {
        "token": "Telegram bot token",
        "admins": [12345678, 87654321],
        "bing_speech_api": ["token1", "token2"],
        "baidu_speech_api": {
            "app_id": 123456,
            "api_key": "APIkey",
            "secret_key": "secret_key"
        }
    }
    """

    def send_message(self, msg: EFBMsg) -> EFBMsg:
        pass

    def get_chats(self) -> List[EFBChat]:
        pass

    def get_chat(self, chat_uid: str, member_uid: Optional[str] = None) -> EFBChat:
        pass

    def send_status(self, status: EFBStatus):
        pass

    def get_chat_picture(self, chat: EFBChat) -> NamedTemporaryFile:
        pass

    # Meta Info
    channel_name = "Telegram Master"
    channel_emoji = "✈"
    channel_id = "eh_telegram_master"
    channel_type = ChannelType.Master
    supported_message_types = {MsgType.Text, MsgType.File, MsgType.Audio,
                               MsgType.Command, MsgType.Image, MsgType.Link, MsgType.Location,
                               MsgType.Sticker, MsgType.Video}

    # Data
    slaves = None
    bot = None
    msg_status = {}
    msg_storage = {}
    me = None
    _stop_polling = False
    timeout_count = 0

    # Constants
    TYPE_DICT = {
        TGMsgType.Text: MsgType.Text,
        TGMsgType.Audio: MsgType.Audio,
        TGMsgType.Document: MsgType.File,
        TGMsgType.Photo: MsgType.Image,
        TGMsgType.Sticker: MsgType.Sticker,
        TGMsgType.Video: MsgType.Video,
        TGMsgType.Voice: MsgType.Audio,
        TGMsgType.Location: MsgType.Location,
        TGMsgType.Venue: MsgType.Location,
    }
    MUTE_CHAT_ID = "{chat_id}.muted"
    CHAT_MODE_EMOJI = {
        "linked": "🔗",
        "muted": "🔇",
        "multi_linked": "🖇️"
    }

    def __init__(self, queue, mutex, slaves):
        """
        Initialization.

        Args:
            queue (queue.Queue): global message queue
            slaves (dict): Dictionary of slaves
        """
        super().__init__(queue, mutex)
        self.slaves = slaves

        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)
        logging.getLogger('telegram.bot').setLevel(logging.CRITICAL)

        try:
            self.bot = telegram.ext.Updater(getattr(config, self.channel_id)['token'])
        except (AttributeError, KeyError):
            raise ValueError("Token is not properly defined. Please define it in `config.py`.")
        mimetypes.init(files=["mimetypes"])
        self.admins = getattr(config, self.channel_id)['admins']
        self.logger = logging.getLogger("plugins.%s.TelegramChannel" % self.channel_id)
        self.me = self.bot.bot.get_me()
        self.bot.dispatcher.add_handler(WhitelistHandler(self.admins))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("link", self.link_chat_show_list, pass_args=True))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("chat", self.start_chat_list, pass_args=True))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("recog", self.recognize_speech, pass_args=True))
        self.bot.dispatcher.add_handler(telegram.ext.CallbackQueryHandler(self.callback_query_dispatcher))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("start", self.start, pass_args=True))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("extra", self.extra_help))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("help", self.help))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("unlink_all", self.unlink_all))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("info", self.info))
        self.bot.dispatcher.add_handler(
            telegram.ext.RegexHandler(r"^/(?P<id>[0-9]+)_(?P<command>[a-z0-9_-]+)", self.extra_call,
                                      pass_groupdict=True))
        self.bot.dispatcher.add_handler(telegram.ext.MessageHandler(
            telegram.ext.Filters.text |
            telegram.ext.Filters.photo |
            telegram.ext.Filters.sticker |
            telegram.ext.Filters.document |
            telegram.ext.Filters.venue |
            telegram.ext.Filters.location |
            telegram.ext.Filters.audio |
            telegram.ext.Filters.voice |
            telegram.ext.Filters.video,
            self.msg
        ))
        self.bot.dispatcher.add_error_handler(self.error)
        self.MUTE_CHAT_ID = self.MUTE_CHAT_ID.format(chat_id=self.channel_id)

    # Truncate string by bytes
    # Written by Mark Tolonen
    # http://stackoverflow.com/a/13738452/1989455

    @staticmethod
    def _utf8_lead_byte(b):
        """A UTF-8 intermediate byte starts with the bits 10xxxxxx."""
        return (b & 0xC0) != 0x80

    def _utf8_byte_truncate(self, text, max_bytes):
        """If text[max_bytes] is not a lead byte, back up until a lead byte is
        found and truncate before that character."""
        utf8 = text.encode('utf8')
        if len(utf8) <= max_bytes:
            return utf8.decode()
        i = max_bytes
        while i > 0 and not self._utf8_lead_byte(utf8[i]):
            i -= 1
        return utf8[:i].decode()

    def callback_query_dispatcher(self, bot, update):
        """
        Dispatch a callback query based on the message session status.

        Args:
            bot (telegram.bot.Bot): bot
            update (telegram.Update): update
        """
        # Get essential information about the query
        query = update.callback_query
        chat_id = query.message.chat.id
        text = query.data
        msg_id = update.callback_query.message.message_id
        msg_status = self.msg_status.get("%s.%s" % (chat_id, msg_id), None)
        # dispatch the query
        if msg_status in [Flags.CONFIRM_LINK]:
            self.link_chat_confirm(bot, chat_id, msg_id, text)
        elif msg_status in [Flags.EXEC_LINK]:
            self.link_chat_exec(bot, chat_id, msg_id, text)
        elif msg_status == Flags.START_CHOOSE_CHAT:
            self.make_chat_head(bot, chat_id, msg_id, text)
        elif msg_status == Flags.COMMAND_PENDING:
            self.command_exec(bot, chat_id, msg_id, text)
        elif msg_status == Flags.SUGGEST_RECIPIENT:
            self.suggested_recipient(bot, chat_id, msg_id, text)
        else:
            bot.editMessageText(text="Session expired. Please try again. (SE01)",
                                chat_id=chat_id,
                                message_id=msg_id)

    @staticmethod
    def _reply_error(bot, update, errmsg):
        """
        A wrap that directly reply a message with error details.

        Returns:
            telegram.Message: Message sent
        """
        return bot.send_message(update.message.chat.id, errmsg, reply_to_message_id=update.message.message_id)

    def process_msg(self, msg):
        """
        Process a message from slave channel and deliver it to the user.

        Args:
            msg (EFBMsg): The message.
        """
        try:
            xid = datetime.datetime.now().timestamp()
            self.logger.debug("%s, Msg text: %s", xid, msg.text)
            self.logger.debug("%s, process_msg_step_0", xid)
            chat_uid = "%s.%s" % (msg.channel_id, msg.origin['uid'])
            tg_chats = db.get_chat_assoc(slave_uid=chat_uid)

            if self.MUTE_CHAT_ID in tg_chats:
                self.logger.info("Received message from muted source: %s (%s)\n[%s] %s",
                                 msg.origin['name'], chat_uid, msg.type, msg.text)
                return

            tg_chat = None
            multi_slaves = False

            if tg_chats:
                tg_chat = tg_chats[0]
                slaves = db.get_chat_assoc(master_uid=tg_chat)
                if slaves and len(slaves) > 1:
                    multi_slaves = True

            msg_prefix = ""  # For group member name
            tg_chat_assoced = False

            if msg.source != ChatType.Group:
                msg.member = {"uid": -1, "name": "", "alias": ""}

            # Generate chat text template & Decide type target
            tg_dest = getattr(config, self.channel_id)['admins'][0]
            self.logger.debug("%s, process_msg_step_1, tg_dest=%s, msg.origin=%s", xid, tg_dest, str(msg.origin))
            if msg.source == ChatType.Group:
                self.logger.debug("msg.member: %s", str(msg.member))
                msg_prefix = msg.member['name'] if msg.member['name'] == msg.member['alias'] or not msg.member['alias'] \
                    else "%s (%s)" % (msg.member['alias'], msg.member['name'])

            if tg_chat:  # if this chat is linked
                tg_dest = int(tg_chat.split('.')[1])
                tg_chat_assoced = True

            if tg_chat and not multi_slaves:  # if singly linked
                if msg_prefix:  # if group message
                    msg_template = "%s:\n" % (msg_prefix)
                else:
                    msg_template = ""
            elif msg.source == ChatType.User:
                emoji_prefix = msg.channel_emoji + utils.Emojis.get_source_emoji(msg.source)
                name_prefix = msg.origin["name"] if msg.origin["alias"] == msg.origin["name"] or not msg.origin['alias'] \
                    else "%s (%s)" % (msg.origin["alias"], msg.origin["name"])
                msg_template = "%s %s:\n" % (emoji_prefix, name_prefix)
            elif msg.source == ChatType.Group:
                emoji_prefix = msg.channel_emoji + utils.Emojis.get_source_emoji(msg.source)
                name_prefix = msg.origin["name"] if msg.origin["alias"] == msg.origin["name"] or not msg.origin['alias'] \
                    else "%s (%s)" % (msg.origin["alias"], msg.origin["name"])
                msg_template = "%s %s [%s]:\n" % (emoji_prefix, msg_prefix, name_prefix)
            elif msg.source == ChatType.System:
                emoji_prefix = msg.channel_emoji + utils.Emojis.get_source_emoji(msg.source)
                name_prefix = msg.origin["name"] if msg.origin["alias"] == msg.origin["name"] or not msg.origin['alias'] \
                    else "%s (%s)" % (msg.origin["alias"], msg.origin["name"])
                msg_template = "%s %s:\n" % (emoji_prefix, name_prefix)
            else:
                msg_template = "Unknown message source (%s):\n" % (msg.source)

            # Type dispatching
            self.logger.debug("%s, process_msg_step_2", xid)
            append_last_msg = False
            if msg.type == MsgType.Text:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.TYPING)
                parse_mode = "HTML" if self._flag("text_as_html", False) else None
                if tg_chat_assoced:
                    last_msg = db.get_last_msg_from_chat(tg_dest)
                    if last_msg:
                        if last_msg.msg_type == "Text":
                            append_last_msg = str(last_msg.slave_origin_uid) == "%s.%s" % (msg.channel_id, msg.origin['uid']) \
                                              and str(last_msg.master_msg_id).startswith(str(tg_dest) + ".") \
                                              and last_msg.sent_to == "master"
                            if msg.source == ChatType.Group:
                                append_last_msg &= str(last_msg.slave_member_uid) == str(msg.member['uid'])
                            append_last_msg &= datetime.datetime.now() - last_msg.time <= datetime.timedelta(
                                seconds=self._flag('join_msg_threshold_secs', 15))
                        else:
                            append_last_msg = False
                    else:
                        append_last_msg = False
                    self.logger.debug("Text: Append last msg: %s", append_last_msg)
                self.logger.debug("%s, process_msg_step_3_0, tg_dest = %s, tg_chat_assoced = %s, append_last_msg = %s",
                                  xid, tg_dest, tg_chat_assoced, append_last_msg)
                if tg_chat_assoced and append_last_msg:
                    self.logger.debug("%s, process_msg_step_3_0_1", xid)
                    msg.text = "%s\n%s" % (last_msg.text, msg.text)
                    try:
                        tg_msg = self.bot.bot.editMessageText(chat_id=tg_dest,
                                                              message_id=last_msg.master_msg_id.split(".", 1)[1],
                                                              text=msg_template + msg.text,
                                                              parse_mode=parse_mode)
                    except telegram.error.BadRequest:
                        tg_msg = self.bot.bot.editMessageText(chat_id=tg_dest,
                                                              message_id=last_msg.master_msg_id.split(".", 1)[1],
                                                              text=msg_template + msg.text)
                else:
                    self.logger.debug("%s, process_msg_step_3_0_3", xid)
                    try:
                        tg_msg = self.bot.bot.send_message(tg_dest,
                                                           text=msg_template + msg.text,
                                                           parse_mode=parse_mode)
                    except telegram.error.BadRequest:
                        tg_msg = self.bot.bot.send_message(tg_dest, text=msg_template + msg.text)
                    self.logger.debug("%s, process_msg_step_3_0_4, tg_msg = %s", xid, tg_msg)
                self.logger.debug("%s, process_msg_step_3_1", xid)
            elif msg.type == MsgType.Link:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.TYPING)
                thumbnail = urllib.parse.quote(msg.attributes["image"] or "", safe="?=&#:/")
                thumbnail = "<a href=\"%s\">🔗</a>" % thumbnail if thumbnail else "🔗"
                text = "%s <a href=\"%s\">%s</a>\n%s" % \
                       (thumbnail,
                        urllib.parse.quote(msg.attributes["url"], safe="?=&#:/"),
                        html.escape(msg.attributes["title"] or msg.attributes["url"]),
                        html.escape(msg.attributes["description"] or ""))
                if msg.text:
                    text += "\n\n" + msg.text
                try:
                    tg_msg = self.bot.bot.send_message(tg_dest,
                                                       text=msg_template + text,
                                                       parse_mode="HTML")
                except telegram.error.BadRequest:
                    text = "🔗 %s\n%s\n\n%s" % (html.escape(msg.attributes["title"] or ""),
                                                html.escape(msg.attributes["description"] or ""),
                                                urllib.parse.quote(msg.attributes["url"] or "", safe="?=&#:/"))
                    if msg.text:
                        text += "\n\n" + msg.text
                    tg_msg = self.bot.bot.send_message(tg_dest, text=msg_template + msg.text)
            elif msg.type in [MsgType.Image, MsgType.Sticker]:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.UPLOAD_PHOTO)
                self.logger.debug("%s, process_msg_step_3_2", xid)
                self.logger.debug("Received %s\nPath: %s\nMIME: %s", msg.type, msg.path, msg.mime)
                self.logger.debug("Path: %s\nSize: %s", msg.path, os.stat(msg.path).st_size)
                if os.stat(msg.path).st_size == 0:
                    os.remove(msg.path)
                    tg_msg = self.bot.bot.send_message(tg_dest,
                                                       msg_template + ("Error: Empty %s received. (MS01)" % msg.type))
                else:
                    if not msg.text:
                        if msg.type == MsgType.Image:
                            msg.text = "sent a picture."
                        elif msg.type == MsgType.Sticker:
                            msg.text = "sent a sticker."
                    if msg.mime == "image/gif":
                        tg_msg = self.bot.bot.sendDocument(tg_dest, msg.file, caption=msg_template + msg.text)
                    else:
                        try:
                            tg_msg = self.bot.bot.sendPhoto(tg_dest, msg.file, caption=msg_template + msg.text)
                        except telegram.error.BadRequest:
                            tg_msg = self.bot.bot.sendDocument(tg_dest, msg.file, caption=msg_template + msg.text)
                    os.remove(msg.path)
                self.logger.debug("%s, process_msg_step_3_3", xid)
            elif msg.type == MsgType.File:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.UPLOAD_DOCUMENT)
                if os.stat(msg.path).st_size == 0:
                    os.remove(msg.path)
                    tg_msg = self.bot.bot.send_message(tg_dest,
                                                     msg_template + ("Error: Empty %s received. (MS02)" % msg.type))
                else:
                    if not msg.filename:
                        file_name = os.path.basename(msg.path)
                        msg.text = "sent a file."
                    else:
                        file_name = msg.filename
                    tg_msg = self.bot.bot.send_document(tg_dest, msg.file, caption=msg_template + msg.text,
                                                        filename=file_name)
                    os.remove(msg.path)
            elif msg.type == MsgType.Audio:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.RECORD_AUDIO)
                if os.stat(msg.path).st_size == 0:
                    os.remove(msg.path)
                    return self.bot.bot.send_message(tg_dest,
                                                     msg_template + ("Error: Empty %s received. (MS03)" % msg.type))
                msg.text = msg.text or ''
                self.logger.debug("%s, process_msg_step_4_1, no_conversion = %s", xid,
                                  self._flag("no_conversion", False))
                if self._flag("no_conversion", False):
                    self.logger.debug("%s, process_msg_step_4_2, mime = %s", xid, msg.mime)
                    if msg.mime == "audio/mpeg":
                        tg_msg = self.bot.bot.sendAudio(tg_dest, msg.file, caption=msg_template + msg.text)
                    else:
                        tg_msg = self.bot.bot.sendDocument(tg_dest, msg.file, caption=msg_template + msg.text)
                else:
                    pydub.AudioSegment.from_file(msg.file).export("%s.ogg" % msg.path,
                                                                  format="ogg",
                                                                  codec="libopus",
                                                                  bitrate="65536")
                    ogg_file = open("%s.ogg" % msg.path, 'rb')
                    tg_msg = self.bot.bot.sendVoice(tg_dest, ogg_file, caption=msg_template + msg.text)
                    os.remove("%s.ogg" % msg.path)
                os.remove(msg.path)
            elif msg.type == MsgType.Location:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.FIND_LOCATION)
                self.logger.info("---\nsending venue\nlat: %s, long: %s\ntitle: %s\naddr: %s",
                                 msg.attributes['latitude'], msg.attributes['longitude'], msg.text, msg_template + "")
                tg_msg = self.bot.bot.sendVenue(tg_dest, latitude=msg.attributes['latitude'],
                                                longitude=msg.attributes['longitude'], title=msg.text,
                                                address=msg_template + "")
            elif msg.type == MsgType.Video:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.UPLOAD_VIDEO)
                if os.stat(msg.path).st_size == 0:
                    os.remove(msg.path)
                    return self.bot.bot.send_message(tg_dest, msg_template + ("Error: Empty %s recieved" % msg.type))
                if not msg.text:
                    msg.text = "sent a video."
                tg_msg = self.bot.bot.sendVideo(tg_dest, msg.file, caption=msg_template + msg.text)
                os.remove(msg.path)
            elif msg.type == MsgType.Command:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.TYPING)
                buttons = []
                for i, ival in enumerate(msg.attributes['commands']):
                    buttons.append([telegram.InlineKeyboardButton(ival['name'], callback_data=str(i))])
                tg_msg = self.bot.bot.send_message(tg_dest, msg_template + msg.text,
                                                   reply_markup=telegram.InlineKeyboardMarkup(buttons))
                self.msg_status["%s.%s" % (tg_dest, tg_msg.message_id)] = Flags.COMMAND_PENDING
                self.msg_storage["%s.%s" % (tg_dest, tg_msg.message_id)] = {"channel": msg.channel_id,
                                                                            "text": msg_template + msg.text,
                                                                            "commands": msg.attributes['commands']}
            else:
                self.bot.bot.send_chat_action(tg_dest, telegram.ChatAction.TYPING)
                tg_msg = self.bot.bot.send_message(tg_dest, msg_template + "Unsupported incoming message type. (UT01)")
            self.logger.debug("%s, process_msg_step_4", xid)
            if msg.source in (ChatType.User, ChatType.Group):
                msg_log = {"master_msg_id": "%s.%s" % (tg_msg.chat.id, tg_msg.message_id),
                           "text": msg.text or "Sent a %s." % msg.type,
                           "msg_type": msg.type,
                           "sent_to": "master",
                           "slave_origin_uid": "%s.%s" % (msg.channel_id, msg.origin['uid']),
                           "slave_origin_display_name": msg.origin['alias'],
                           "slave_member_uid": msg.member['uid'],
                           "slave_member_display_name": msg.member['alias'],
                           "slave_message_id": msg.uid}
                if tg_chat_assoced and append_last_msg:
                    msg_log['update'] = True
                db.add_msg_log(**msg_log)
            self.logger.debug("%s, process_msg_step_5", xid)
        except Exception as e:
            self.logger.error(repr(e) + traceback.format_exc())

    @staticmethod
    def _db_slave_chat_info_as_dict(channel_id, chat_id):
        d = db.get_slave_chat_info(slave_channel_id=channel_id, slave_chat_uid=chat_id)
        if d:
            return {
                "name": d.slave_chat_name,
                "alias": d.slave_chat_alias,
                "uid": d.slave_chat_uid,
                "type": d.slave_chat_type,
            }

    def slave_chats_pagination(self, storage_id, offset=0, filter="", fchats=None):
        """
        Generate a list of (list of) `InlineKeyboardButton`s of chats in slave channels,
        based on the status of message located by `storage_id` and the paging from
        `offset` value.

        Args:
            filter: Regular expression filter for chat details
            storage_id (str): Message_storage ID for generating the buttons list.
            offset (int): Offset for pagination
            fchats (list of str): A list of chats used to generate the pagination list.
                Each str is in the format of "{channel_id}.{chat_uid}".

        Returns:
            tuple (list of str, list of list of InlineKeyboardButton):
                A tuple: legend, chat_btn_list
                `legend` is the legend of all Emoji headings in the entire list.
                `chat_btn_list` is a list which can be fit into `telegram.InlineKeyboardMarkup`.
        """
        self.logger.debug("slave_chats_pagination:\nstorage = %s\noffset = %s\nfilter = %s\nfchats = %s",
                          storage_id,
                          offset,
                          filter,
                          fchats)
        legend = [
            "%s: Linked" % self.CHAT_MODE_EMOJI['linked'],
            "%s: Muted" % self.CHAT_MODE_EMOJI['muted'],
            "%s: User" % utils.Emojis.USER_EMOJI,
            "%s: Group" % utils.Emojis.GROUP_EMOJI,
        ]

        if self.msg_storage.get(storage_id, None):
            chats = self.msg_storage[storage_id]['chats']
            channels = self.msg_storage[storage_id]['channels']
            count = self.msg_storage[storage_id]['count']
        else:
            rfilter = filter and re.compile(filter, re.DOTALL | re.IGNORECASE)
            if filter:
                self.logger.debug("Filter string: %s", filter)
            chats = []
            channels = {}
            if fchats:
                slaves = set()
                for i in fchats:
                    channel_id, chat_uid = i.split('.', 1)
                    slaves.add(channel_id)
                    channel = self.slaves[channel_id]
                    try:
                        chat = self._db_slave_chat_info_as_dict(channel_id, chat_uid) or channel.get_chat(chat_uid)
                    except KeyError:
                        self.logger.error("slave_chats_pagination with chats list: Chat %s not found.", i)
                        continue
                    c = self._make_chat_dict(channel, chat, rfilter)
                    if c:
                        chats.append(c)
                for slave_id in self.slaves:
                    slave = self.slaves[slave_id]
                    channels[slave.channel_id] = {
                        "channel_name": slave.channel_name,
                        "channel_emoji": slave.channel_emoji
                    }
            else:
                for slave_id in self.slaves:
                    slave = self.slaves[slave_id]
                    slave_chats = slave.get_chats()
                    channels[slave.channel_id] = {
                        "channel_name": slave.channel_name,
                        "channel_emoji": slave.channel_emoji
                    }
                    for chat in slave_chats:
                        c = self._make_chat_dict(slave, chat, rfilter)
                        if c:
                            chats.append(c)
            count = len(chats)
            self.msg_storage[storage_id] = {
                "offset": offset,
                "count": len(chats),
                "chats": chats.copy(),
                "channels": channels.copy()
            }

        threading.Thread(target=self._db_update_slave_chats_cache, args=(chats.copy(), )).start()

        for ch in channels:
            legend.append("%s: %s" % (channels[ch]['channel_emoji'], channels[ch]['channel_name']))

        # Build inline button list
        chat_btn_list = []
        chats_per_page = self._flag("chats_per_page", 10)
        for i in range(offset, min(offset + chats_per_page, count)):
            chat = chats[i]
            if chat['muted']:
                mode = self.CHAT_MODE_EMOJI['muted']
            elif chat['linked']:
                mode = self.CHAT_MODE_EMOJI['linked']
            else:
                mode = ""
            chat_type = utils.Emojis.get_source_emoji(chat['type'])
            chat_name = chat['chat_alias'] if chat['chat_name'] == chat['chat_alias'] else "%s (%s)" % (
            chat['chat_alias'], chat['chat_name'])
            button_text = "%s%s%s: %s" % (chat['channel_emoji'], chat_type, mode, chat_name)
            button_callback = "chat %s" % i
            chat_btn_list.append([telegram.InlineKeyboardButton(button_text, callback_data=button_callback)])

        # Pagination
        page_number_row = []

        if offset - chats_per_page >= 0:
            page_number_row.append(telegram.InlineKeyboardButton("< Prev", callback_data="offset %s" % (
                offset - chats_per_page)))
        page_number_row.append(telegram.InlineKeyboardButton("Cancel", callback_data=Flags.CANCEL_PROCESS))
        if offset + chats_per_page < count:
            page_number_row.append(telegram.InlineKeyboardButton("Next >", callback_data="offset %s" % (
                offset + chats_per_page)))
        chat_btn_list.append(page_number_row)

        return legend, chat_btn_list

    def _db_update_slave_chats_cache(self, chats):
        """
        Update all slave chats info cache to database. Triggered by retrieving
        the entire list of chats from all slaves by the method `slave_chats_pagination`.

        Args:
            chats (list of dict): a list of dicts generated by method `_make_chat_dict`
        """
        for i in chats:
            db.set_slave_chat_info(slave_channel_id=i['channel_id'],
                                   slave_channel_name=i['channel_name'],
                                   slave_channel_emoji=i['channel_emoji'],
                                   slave_chat_uid=i['chat_uid'],
                                   slave_chat_name=i['chat_name'],
                                   slave_chat_alias=i['chat_alias'],
                                   slave_chat_type=i['type'])

    def _make_chat_dict(self, channel, chat, rfilter=None):
        """
        Check the chat against a regex filter and return the full
        info dict if it matches, None otherwise.
        Args:
            channel (EFBChannel): The chat channel
            chat (dict): A standard chat dict
            rfilter (_sre.SRE_Pattern): The `re.compile` regex pattern. To allow all results,
                use anything that evaluate to False.

        Returns:
            dict|None: The "full info" dict or None.
                Sample:
                    {
                        "channel_id": channel.channel_id,
                        "channel_name": channel.channel_name,
                        "channel_emoji": channel.channel_emoji,
                        "chat_name": chat['name'],
                        "chat_alias": chat['alias'],
                        "chat_uid": chat['uid'],
                        "type": chat['type'],
                        "muted": muted,
                        "linked": not muted and len(chat_assoc)
                    }
        """
        chat_assoc = db.get_chat_assoc(slave_uid="%s.%s" % (channel.channel_id, chat['uid']))
        muted = self.MUTE_CHAT_ID in chat_assoc
        c = {
            "channel_id": channel.channel_id,
            "channel_name": channel.channel_name,
            "channel_emoji": channel.channel_emoji,
            "chat_name": chat['name'],
            "chat_alias": chat['alias'],
            "chat_uid": chat['uid'],
            "type": chat['type'],
            "muted": muted,
            "linked": not muted and len(chat_assoc)
        }
        if not rfilter:
            return c
        mode = []
        if c['muted']: mode.append("Muted")
        if c['linked']: mode.append("Linked")
        entry_string = "Channel: %s\nName: %s\nAlias: %s\nID: %s\nType: %s\nMode: %s" \
                       % (c['channel_name'],
                          c['chat_name'],
                          c['chat_alias'],
                          c['chat_uid'],
                          c['type'],
                          mode)
        if rfilter.search(entry_string):
            return c

    def link_chat_show_list(self, bot, update, args=None):
        """
        Show the list of available chats for linking.
        Triggered by `/link`.

        Args:
            bot: Telegram Bot instance
            update: Message update
        """
        args = args or []
        if update.message.from_user.id != update.message.chat_id:
            links = db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat_id))
            if links:
                return self.link_chat_gen_list(bot, update.message.chat_id, filter=" ".join(args), chats=links)

        self.link_chat_gen_list(bot, update.message.from_user.id, filter=" ".join(args))

    def link_chat_gen_list(self, bot, chat_id, message_id=None, offset=0, filter="", chats=None):
        """
        Generate the list for chat linking, and update it to a message.

        Args:
            bot: Telegram Bot instance
            chat_id: Chat ID
            message_id: ID of message to be updated, None to send a new message.
            offset: Offset for pagination.
            filter (str): Regex expression to filter chats.
            chats (list of str): Specified chats to link
        """
        if not message_id:
            message_id = bot.send_message(chat_id, "Processing...").message_id
        bot.send_chat_action(chat_id, telegram.ChatAction.TYPING)
        if chats:
            msg_text = "This Telegram group is currently linked with the following remote groups."
        else:
            msg_text = "Please choose the chat you want to link with..."
        msg_text += "\n\nLegend:\n"

        legend, chat_btn_list = self.slave_chats_pagination("%s.%s" % (chat_id, message_id),
                                                            offset,
                                                            filter=filter,
                                                            fchats=chats)
        for i in legend:
            msg_text += "%s\n" % i

        msg = bot.editMessageText(chat_id=chat_id, message_id=message_id, text=msg_text,
                                  reply_markup=telegram.InlineKeyboardMarkup(chat_btn_list))
        self.msg_status["%s.%s" % (chat_id, msg.message_id)] = Flags.CONFIRM_LINK

    def link_chat_confirm(self, bot, tg_chat_id, tg_msg_id, callback_uid):
        """
        Confirmation of chat linking. Triggered by callback message on status `Flags.CONFIRM_LINK`.

        Args:
            bot: Telegram Bot instance
            tg_chat_id: Chat ID
            tg_msg_id: Message ID triggered the callback
            callback_uid: Callback message
        """
        if callback_uid.split()[0] == "offset":
            return self.link_chat_gen_list(bot, tg_chat_id, message_id=tg_msg_id, offset=int(callback_uid.split()[1]))
        if callback_uid == Flags.CANCEL_PROCESS:
            txt = "Cancelled."
            self.msg_status.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            self.msg_storage.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            return bot.editMessageText(text=txt,
                                       chat_id=tg_chat_id,
                                       message_id=tg_msg_id)
        if callback_uid[:4] != "chat":
            txt = "Invalid parameter (%s). (IP01)" % callback_uid
            self.msg_status.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            self.msg_storage.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            return bot.editMessageText(text=txt,
                                       chat_id=tg_chat_id,
                                       message_id=tg_msg_id)

        callback_uid = int(callback_uid.split()[1])
        chat = self.msg_storage["%s.%s" % (tg_chat_id, tg_msg_id)]['chats'][callback_uid]
        chat_uid = "%s.%s" % (chat['channel_id'], chat['chat_uid'])
        chat_display_name = chat['chat_name'] if chat['chat_name'] == chat['chat_alias'] else "%s (%s)" % (
        chat['chat_alias'], chat['chat_name'])
        chat_display_name = "'%s' from '%s %s'" % (chat_display_name, chat['channel_emoji'], chat['channel_name'])

        linked = db.get_chat_assoc(slave_uid=chat_uid)
        muted = self.MUTE_CHAT_ID in linked
        self.msg_status["%s.%s" % (tg_chat_id, tg_msg_id)] = Flags.EXEC_LINK
        self.msg_storage["%s.%s" % (tg_chat_id, tg_msg_id)] = {
            "chat_uid": chat_uid,
            "chat_display_name": chat_display_name,
            "chats": [chat.copy()],
            "tg_chat_id": tg_chat_id,
            "tg_msg_id": tg_msg_id
        }
        txt = "You've selected chat %s." % chat_display_name
        if muted:
            txt += "\nThis chat is currently muted."
        elif linked:
            txt += "\nThis chat has already linked to Telegram."
        txt += "\nWhat would you like to do?"

        link_url = "https://telegram.me/%s?startgroup=%s" % (
            self.me.username, urllib.parse.quote(self.b64en("%s.%s" % (tg_chat_id, tg_msg_id))))
        self.logger.debug("Telegram start trigger for linking chat: %s", link_url)
        if linked and not muted:
            btn_list = [telegram.InlineKeyboardButton("Relink", url=link_url),
                        telegram.InlineKeyboardButton("Mute", callback_data="mute 0"),
                        telegram.InlineKeyboardButton("Restore", callback_data="unlink 0")]
        elif muted:
            btn_list = [telegram.InlineKeyboardButton("Link", url=link_url),
                        telegram.InlineKeyboardButton("Unmute", callback_data="unlink 0")]
        else:
            btn_list = [telegram.InlineKeyboardButton("Link", url=link_url),
                        telegram.InlineKeyboardButton("Mute", callback_data="mute 0")]
        btn_list.append(telegram.InlineKeyboardButton("Cancel", callback_data=Flags.CANCEL_PROCESS))

        bot.editMessageText(text=txt,
                            chat_id=tg_chat_id,
                            message_id=tg_msg_id,
                            reply_markup=telegram.InlineKeyboardMarkup([btn_list]))

    def link_chat_exec(self, bot, tg_chat_id, tg_msg_id, callback_uid):
        """
        Action to link a chat. Triggered by callback message with status `Flags.EXEC_LINK`.

        Args:
            bot: Telegram Bot instance
            tg_chat_id: Chat ID
            tg_msg_id: Message ID triggered the callback
            callback_uid: Callback message
        """
        if callback_uid == Flags.CANCEL_PROCESS:
            txt = "Cancelled."
            self.msg_status.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            self.msg_storage.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)

            return bot.editMessageText(text=txt,
                                       chat_id=tg_chat_id,
                                       message_id=tg_msg_id)
        cmd, chat_lid = callback_uid.split()
        chat = self.msg_storage["%s.%s" % (tg_chat_id, tg_msg_id)]['chats'][int(chat_lid)]
        chat_uid = "%s.%s" % (chat['channel_id'], chat['chat_uid'])
        chat_display_name = chat['chat_name'] if chat['chat_name'] == chat['chat_alias'] else "%s (%s)" % (
            chat['chat_alias'], chat['chat_name'])
        chat_display_name = "'%s' from '%s %s'" % (chat_display_name, chat['channel_emoji'], chat['channel_name']) \
            if chat['channel_name'] else "'%s'" % chat_display_name
        self.msg_status.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
        self.msg_storage.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
        if cmd == "unlink":
            db.remove_chat_assoc(slave_uid=chat_uid)
            txt = "Chat %s is restored." % chat_display_name
            return bot.editMessageText(text=txt, chat_id=tg_chat_id, message_id=tg_msg_id)
        if cmd == "mute":
            db.remove_chat_assoc(slave_uid=chat_uid)
            db.add_chat_assoc(slave_uid=chat_uid, master_uid=self.MUTE_CHAT_ID, multiple_slave=True)
            txt = "Chat %s is now muted." % chat_display_name
            return bot.editMessageText(text=txt, chat_id=tg_chat_id, message_id=tg_msg_id)
        txt = "Command '%s' (%s) is not recognised, please try again" % (cmd, callback_uid)
        bot.editMessageText(text=txt, chat_id=tg_chat_id, message_id=tg_msg_id)

    def unlink_all(self, bot, update):
        """
        Unlink all chats linked to the telegram group.
        Triggered by `/unlink_all`.

        Args:
            bot: Telegram Bot instance
            update: Message update
        """
        if update.message.chat.id == update.message.from_user.id:
            return bot.send_message(update.message.chat.id, "Send `/unlink_all` to a group to unlink all remote chats "
                                                           "from it.",
                                   parse_mode=telegram.ParseMode.MARKDOWN,
                                   reply_to_message_id=update.message.message_id)
        assocs = db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id))
        if len(assocs) < 1:
            return bot.send_message(update.message.chat.id, "No chat is linked to the group.",
                                   reply_to_message_id=update.message.message_id)
        else:
            db.remove_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id))
            return bot.send_message(update.message.chat.id, "All chats has been unlinked from this group. (%s)" % len(assocs),
                                   reply_to_message_id=update.message.message_id)

    def info(self, bot, update):
        """
        Show info of the current telegram conversation.
        Triggered by `/info`.

        Args:
            bot: Telegram Bot instance
            update: Message update
        """
        if update.message.chat_id == update.message.from_user.id:  # Talking to the bot.
            msg = "This is EFB Telegram Master Channel, " \
                  "you currently have %s slave channels activated:" % len(self.slaves)
            for i in self.slaves:
                msg += "\n- %s %s (%s)" % (self.slaves[i].channel_emoji,
                                           self.slaves[i].channel_name,
                                           i)
        else:
            links = db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat_id))
            if links:  # Linked chat
                msg = "The group {group_name} ({group_id}) is " \
                      "linked to the following chat(s):".format(group_name=update.message.chat.title,
                                                                group_id=update.message.chat_id)
                for i in links:
                    channel_id, chat_id = i.split('.', 1)
                    d = self._db_slave_chat_info_as_dict(channel_id, chat_id)
                    try:
                        if not d:
                            d = self.slaves[channel_id].get_chat(chat_id)
                            self._db_update_slave_chats_cache([self._make_chat_dict(self.slaves[channel_id], d, None)])
                        msg += "\n- {channel_emoji}{chat_type_emoji} {channel_name}: {chat_name}".format(
                            channel_emoji=self.slaves[channel_id].channel_emoji,
                            chat_type_emoji=utils.Emojis.get_source_emoji(d['type']),
                            channel_name=self.slaves[channel_id].channel_name,
                            chat_name=d['name'] if not d['alias'] or d['alias'] == d['name'] else "%s (%s)" % (d['alias'], d['name'])
                        )
                    except KeyError:
                        msg += "\n- {channel_emoji} {channel_name}: Unknown chat ({chat_id})".format(
                            channel_emoji=self.slaves[channel_id].channel_emoji,
                            channel_name=self.slaves[channel_id].channel_name,
                            chat_id=chat_id
                        )
            else:
                msg = "The group {group_name} ({group_id}) is not linked to any remote chat. " \
                      "To link one, use /link.".format(group_name=update.message.chat.title,
                                                       group_id=update.message.chat_id)

        update.message.reply_text(msg)

    def start_chat_list(self, bot, update, args=None):
        """
        Send a list to for chat list generation.
        Triggered by `/list`.

        Args:
            bot: Telegram Bot instance
            update: Message update
            args: Arguments from the command message
        """
        args = args or []
        chats = None
        if update.message.from_user.id != update.message.chat_id:
            chats = db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat_id))
            chats = chats or None
        if chats:
            target = update.message.chat_id
        else:
            target = update.message.from_user.id
        self.chat_head_req_generate(bot, target, filter=" ".join(args), chats=chats)

    def chat_head_req_generate(self, bot, chat_id, message_id=None, offset=0, filter="", chats=None):
        """
        Generate the list for chat head, and update it to a message.

        Args:
            bot: Telegram Bot instance
            chat_id: Chat ID
            message_id: ID of message to be updated, None to send a new message.
            offset: Offset for pagination.
            filter: Regex String used as a filter.
            chats: Specified lint of chats to start a chat head.
        """
        if not message_id:
            message_id = bot.send_message(chat_id, text="Processing...").message_id
        bot.send_chat_action(chat_id, telegram.ChatAction.TYPING)

        if chats and len(chats):
            if len(chats) == 1:
                slave_channel_id, slave_chat_id = chats[0].split('.', 1)
                channel = self.slaves[slave_channel_id]
                try:
                    chat = self._db_slave_chat_info_as_dict(slave_channel_id, slave_chat_id) or channel.get_chat(slave_chat_id)
                    msg_text = "This group is linked to {channel_emoji}{chat_type_emoji} {channel_name}: " \
                               "{chat_name}. Send a message to this group to deliver it to the chat.\n" \
                               "Do NOT reply to this system message.".format(
                                    channel_emoji=channel.channel_emoji,
                                    chat_type_emoji=utils.Emojis.get_source_emoji(chat['type']),
                                    channel_name=channel.channel_name,
                                    chat_name=chat['name'] if not chat['alias'] or chat['alias'] == chat['name'] else "%s (%s)" % (chat['alias'], chat['name'])
                                )
                except KeyError:
                    msg_text = "This group is linked to an unknown chat ({chat_id}) "\
                               "on channel {channel_emoji} {channel_name}. Possibly you can "\
                               "no longer reach this chat. Send /unlink_all to unlink all chats "\
                               "from this group.".format(
                                    channel_emoji=channel.channel_emoji,
                                    channel_name=channel.channel_name,
                                    chat_id=slave_chat_id
                               )
                return bot.editMessageText(text=msg_text,
                                           chat_id=chat_id,
                                           message_id=message_id)
            else:
                msg_text = "This Telegram group is linked to the following chats, " \
                           "choose one to start a conversation with."
        else:
            msg_text = "Choose a chat you want to start a conversation with."

        legend, chat_btn_list = self.slave_chats_pagination("%s.%s" % (chat_id, message_id), offset, filter=filter, fchats=chats)

        msg_text += "\n\nLegend:\n"
        for i in legend:
            msg_text += "%s\n" % i
        bot.editMessageText(text=msg_text,
                            chat_id=chat_id,
                            message_id=message_id,
                            reply_markup=telegram.InlineKeyboardMarkup(chat_btn_list))
        self.msg_status["%s.%s" % (chat_id, message_id)] = Flags.START_CHOOSE_CHAT

    def make_chat_head(self, bot, tg_chat_id, tg_msg_id, callback_uid):
        """
        Create a chat head. Triggered by callback message with status `Flags.START_CHOOSE_CHAT`.

        Args:
            bot: Telegram Bot instance
            tg_chat_id: Chat ID
            tg_msg_id: Message ID triggered the callback
            callback_uid: Callback message
        """
        if callback_uid.split()[0] == "offset":
            return self.chat_head_req_generate(bot, tg_chat_id, message_id=tg_msg_id,
                                               offset=int(callback_uid.split()[1]))
        if callback_uid == Flags.CANCEL_PROCESS:
            txt = "Cancelled."
            self.msg_status.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            self.msg_storage.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            return bot.editMessageText(text=txt,
                                       chat_id=tg_chat_id,
                                       message_id=tg_msg_id)

        if callback_uid[:4] != "chat":
            txt = "Invalid parameter. (%s)" % callback_uid
            self.msg_status.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            self.msg_storage.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
            return bot.editMessageText(text=txt,
                                       chat_id=tg_chat_id,
                                       message_id=tg_msg_id)
        callback_uid = int(callback_uid.split()[1])
        chat = self.msg_storage["%s.%s" % (tg_chat_id, tg_msg_id)]['chats'][callback_uid]
        chat_uid = "%s.%s" % (chat['channel_id'], chat['chat_uid'])
        chat_display_name = chat['chat_name'] if chat['chat_name'] == chat['chat_alias'] else "%s (%s)" % (
            chat['chat_alias'], chat['chat_name'])
        chat_display_name = "'%s' from '%s %s'" % (chat_display_name, chat['channel_emoji'], chat['channel_name'])
        self.msg_status.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
        self.msg_storage.pop("%s.%s" % (tg_chat_id, tg_msg_id), None)
        txt = "Reply to this message to chat with %s." % chat_display_name
        msg_log = {"master_msg_id": "%s.%s" % (tg_chat_id, tg_msg_id),
                   "text": txt,
                   "msg_type": "Text",
                   "sent_to": "master",
                   "slave_origin_uid": chat_uid,
                   "slave_origin_display_name": chat_display_name,
                   "slave_member_uid": None,
                   "slave_member_display_name": None,
                   "slave_message_id": "__chathead__"}
        db.add_msg_log(**msg_log)
        bot.editMessageText(text=txt, chat_id=tg_chat_id, message_id=tg_msg_id)

    def command_exec(self, bot, chat_id, message_id, callback):
        """
        Run a command from a command message.
        Triggered by callback message with status `Flags.COMMAND_PENDING`.

        Args:
            bot: Telegram Bot instance
            chat_id: Chat ID
            message_id: Message ID triggered the callback
            callback: Callback message
        """
        if not callback.isdecimal():
            msg = "Invalid parameter: %s. (CE01)" % callback
            self.msg_status.pop("%s.%s" % (chat_id, message_id), None)
            self.msg_storage.pop("%s.%s" % (chat_id, message_id), None)
            return bot.editMessageText(text=msg, chat_id=chat_id, message_id=message_id)
        elif not (0 <= int(callback) < len(self.msg_storage["%s.%s" % (chat_id, message_id)])):
            msg = "Index out of bound: %s. (CE02)" % callback
            self.msg_status.pop("%s.%s" % (chat_id, message_id), None)
            self.msg_storage.pop("%s.%s" % (chat_id, message_id), None)
            return bot.editMessageText(text=msg, chat_id=chat_id, message_id=message_id)

        callback = int(callback)
        channel_id = self.msg_storage["%s.%s" % (chat_id, message_id)]['channel']
        command = self.msg_storage["%s.%s" % (chat_id, message_id)]['commands'][callback]
        msg = self.msg_storage["%s.%s" % (chat_id, message_id)]['text'] + "\n------\n" + getattr(
            self.slaves[channel_id], command['callable'])(*command['args'], **command['kwargs'])
        self.msg_status.pop("%s.%s" % (chat_id, message_id), None)
        self.msg_storage.pop("%s.%s" % (chat_id, message_id), None)
        return bot.editMessageText(text=msg, chat_id=chat_id, message_id=message_id)

    def extra_help(self, bot, update):
        """
        Show list of extra functions and their usage.
        Triggered by `/extra`.

        Args:
            bot: Telegram Bot instance
            update: Message update
        """
        msg = "List of slave channel features:"
        for n, i in enumerate(sorted(self.slaves)):
            i = self.slaves[i]
            msg += "\n\n<b>%s %s</b>" % (i.channel_emoji, i.channel_name)
            xfns = i.get_extra_functions()
            if xfns:
                for j in xfns:
                    fn_name = "/%s_%s" % (n, j)
                    msg += "\n\n%s <b>(%s)</b>\n%s" % (
                    fn_name, xfns[j].name, xfns[j].desc.format(function_name=fn_name))
            else:
                msg += "No command found."
        bot.send_message(update.message.chat.id, msg, parse_mode="HTML")

    def extra_call(self, bot, update, groupdict=None):
        """
        Call an extra function from slave channel.

        Args:
            bot: Telegram Bot instance
            update: Message update
            groupdict: Parameters offered by the message
        """
        if int(groupdict['id']) >= len(self.slaves):
            return self._reply_error(bot, update, "Invalid slave channel ID. (XC01)")
        ch = self.slaves[sorted(self.slaves)[int(groupdict['id'])]]
        fns = ch.get_extra_functions()
        if groupdict['command'] not in fns:
            return self._reply_error(bot, update, "Command not found in selected channel. (XC02)")
        header = "%s %s: %s\n-------\n" % (ch.channel_emoji, ch.channel_name, fns[groupdict['command']].name)
        msg = bot.send_message(update.message.chat.id, header + "Please wait...")
        result = fns[groupdict['command']](" ".join(update.message.text.split(' ', 1)[1:]))
        bot.editMessageText(text=header + result, chat_id=update.message.chat.id, message_id=msg.message_id)

    def msg(self, bot, update):
        """
        Process, wrap and deliver messages from user.

        Args:
            bot: Telegram Bot instance
            update: Message update
        """
        self.logger.debug("----\nMsg from tg user:\n%s", update.message.to_dict())
        multi_slaves = False

        if update.message.chat.id != update.message.from_user.id:  # from group
            assocs = db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id))
            if len(assocs) > 1:
                multi_slaves = True

        reply_to = bool(getattr(update.message, "reply_to_message", None))
        private_chat = update.message.chat.id == update.message.from_user.id

        if (private_chat or multi_slaves) and not reply_to:
            candidates = db.get_recent_slave_chats(update.message.chat.id) or\
                         db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id))[:5]
            if candidates:
                tg_err_msg = update.message.reply_text("Error: No recipient specified.\n"
                                                       "Please reply to a previous message.", quote=True)
                storage_id = "%s.%s" % (update.message.chat.id, tg_err_msg.message_id)
                legends, buttons = self.slave_chats_pagination(storage_id, 0, fchats=candidates)
                tg_err_msg.edit_text("Error: No recipient specified.\n"
                                     "Please reply to a previous message, "
                                     "or choose a recipient:\n\nLegend:\n" + "\n".join(legends),
                                     reply_markup=telegram.InlineKeyboardMarkup(buttons))
                self.msg_status[storage_id] = Flags.SUGGEST_RECIPIENT
                self.msg_storage[storage_id]["update"] = update.to_dict()
            else:
                update.message.reply_text("Error: No recipient specified.\n"
                                          "Please reply to a previous message.", quote=True)
        else:
            return self.process_telegram_message(bot, update)

    def suggested_recipient(self, bot, chat_id, msg_id, param):
        storage_id = "%s.%s" % (chat_id, msg_id)
        if param.startswith("chat "):
            update = telegram.update.Update.de_json(self.msg_storage[storage_id]["update"], bot)
            chat = self.msg_storage[storage_id]['chats'][int(param.split(' ', 1)[1])]
            self.process_telegram_message(bot, update, channel_id=chat['channel_id'], chat_id=chat['chat_uid'])
            bot.edit_message_text("Delivering the message to %s%s %s: %s." % (chat['channel_emoji'],
                                                                              utils.Emojis.get_source_emoji(chat['type']),
                                                                              chat['channel_name'],
                                                                              chat['chat_name'] if not chat['chat_alias'] or chat['chat_alias'] == chat['chat_name'] else "%s (%s)" % (chat['chat_alias'], chat['chat_name'])),
                                  chat_id=chat_id,
                                  message_id=msg_id)
        elif param == Flags.CANCEL_PROCESS:
            bot.edit_message_text("Error: No recipient specified.\n"
                                  "Please reply to a previous message.",
                                  chat_id=chat_id,
                                  message_id=msg_id)
        else:
            bot.edit_message_text("Error: No recipient specified.\n"
                                  "Please reply to a previous message.\n\n"
                                  "Invalid parameter (%s)." % param,
                                  chat_id=chat_id,
                                  message_id=msg_id)

    def process_telegram_message(self, bot, update, channel_id=None, chat_id=None, target_msg=None):
        self.logger.debug("----\nMsg from tg user:\n%s", update.message.to_dict())
        target = None
        multi_slaves = False
        assoc = None
        slave_msg = None

        if update.message.chat.id != update.message.from_user.id:  # from group
            assocs = db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id))
            if len(assocs) == 1:
                assoc = assocs[0]
            elif len(assocs) > 1:
                multi_slaves = True

        reply_to = bool(getattr(update.message, "reply_to_message", None))
        private_chat = update.message.chat.id == update.message.from_user.id

        if channel_id and chat_id:
            assoc = "%s.%s" % (channel_id, chat_id)
            if target_msg:
                try:
                    targetlog = db.get_msg_log(target_msg)
                    target = targetlog.slave_origin_uid
                    targetChannel, targetUid = target.split('.', 1)
                except:
                    return self._reply_error(bot, update,
                                             "Message is not found in database. "
                                             "Please try with another message. (UC07)")
        elif private_chat:
            if reply_to:
                try:
                    assoc = db.get_msg_log("%s.%s" % (
                        update.message.reply_to_message.chat.id,
                        update.message.reply_to_message.message_id)).slave_origin_uid
                except:
                    return self._reply_error(bot, update,
                                             "Message is not found in database. Please try with another one. (UC03)")
            else:
                return self._reply_error(bot, update,
                                         "Please reply to an incoming message. (UC04)")
        else:  # group chat
            if multi_slaves:
                if reply_to:
                    try:
                        assoc = db.get_msg_log("%s.%s" % (
                            update.message.reply_to_message.chat.id,
                            update.message.reply_to_message.message_id)).slave_origin_uid
                    except:
                        return self._reply_error(bot, update,
                                                 "Message is not found in database. "
                                                 "Please try with another one. (UC05)")
                else:
                    return self._reply_error(bot, update,
                                             "This group is linked to multiple remote chats. "
                                             "Please reply to an incoming message. "
                                             "To unlink all remote chats, please send /unlink_all . (UC06)")
            elif assoc:
                if reply_to:
                    try:
                        targetlog = db.get_msg_log(
                            "%s.%s" % (
                                update.message.reply_to_message.chat.id, update.message.reply_to_message.message_id))
                        target = targetlog.slave_origin_uid
                        targetChannel, targetUid = target.split('.', 1)
                    except:
                        return self._reply_error(bot, update,
                                                 "Message is not found in database. "
                                                 "Please try with another message. (UC07)")
            else:
                return self._reply_error(bot, update,
                                         "This group is not linked to any chat. (UC06)")

        self.logger.debug("Destination chat = %s", assoc)
        channel, uid = assoc.split('.', 2)
        if channel not in self.slaves:
            return self._reply_error(bot, update, "Internal error: Channel not found.")

        try:
            m = EFBMsg(self)
            m.uid = "%s.%s" % (update.message.chat.id, update.message.message_id)
            mtype = get_msg_type(update.message)
            # Chat and author related stuff
            m.origin['uid'] = update.message.from_user.id
            if getattr(update.message.from_user, "last_name", None):
                m.origin['alias'] = "%s %s" % (update.message.from_user.first_name, update.message.from_user.last_name)
            else:
                m.origin['alias'] = update.message.from_user.first_name
            if getattr(update.message.from_user, "username", None):
                m.origin['name'] = "@%s" % update.message.from_user.id
            else:
                m.origin['name'] = m.origin['alias']
            m.destination = {
                'channel': channel,
                'uid': uid,
                'name': '',
                'alias': ''
            }
            if target:
                if targetChannel == channel:
                    trgtMsg = EFBMsg(self.slaves[targetChannel])
                    trgtMsg.type = MsgType.Text
                    trgtMsg.text = targetlog.text
                    trgtMsg.uid = targetlog.slave_message_id
                    if targetlog.slave_member_uid:
                        trgtMsg.member = {
                            "name": targetlog.slave_member_display_name,
                            "alias": targetlog.slave_member_display_name,
                            "uid": targetlog.slave_member_uid
                        }
                    trgtMsg.origin = {
                        "name": targetlog.slave_origin_display_name,
                        "alias": targetlog.slave_origin_display_name,
                        "uid": targetlog.slave_origin_uid.split('.', 1)[1]
                    }
                    m.target = {
                        "type": TargetType.Message,
                        "target": trgtMsg
                    }
            # Type specific stuff
            self.logger.debug("Msg type: %s", mtype)

            if self.TYPE_DICT.get(mtype, None):
                m.type = self.TYPE_DICT[mtype]
            else:
                raise EFBMessageTypeNotSupported()

            if m.type not in self.slaves[channel].supported_message_types:
                raise EFBMessageTypeNotSupported()

            if mtype == TGMsgType.Text:
                m.type = MsgType.Text
                m.text = update.message.text
            elif mtype == TGMsgType.Photo:
                m.type = MsgType.Image
                m.text = update.message.caption
                m.path, m.mime = self._download_file(update.message, update.message.photo[-1], m.type)
                m.file = open(m.path, "rb")
            elif mtype == TGMsgType.Sticker:
                m.type = MsgType.Sticker
                m.text = ""
                m.path, m.mime = self._download_file(update.message, update.message.sticker, m.type)
                m.file = open(m.path, "rb")
            elif mtype == TGMsgType.Document:
                m.text = update.message.caption
                self.logger.debug("tg: Document file received")
                m.filename = getattr(update.message.document, "file_name", None) or None
                if update.message.document.mime_type == "video/mp4":
                    self.logger.debug("tg: Telegram GIF received")
                    m.type = MsgType.Image
                    m.path, m.mime = self._download_gif(update.message, update.message.document, m.type)
                else:
                    m.type = MsgType.File
                    m.path, m.mime = self._download_file(update.message, update.message.document, m.type)
                    m.mime = update.message.document.mime_type or m.mime
                m.file = open(m.path, "rb")
            elif mtype == TGMsgType.Video:
                m.type = MsgType.Video
                m.text = update.message.caption
                m.path, m.mime = self._download_file(update.message, update.message.video, m.type)
                m.file = open(m.path, "rb")
            elif mtype == TGMsgType.Audio:
                m.type = MsgType.Audio
                m.text = "%s - %s\n%s" % (
                    update.message.audio.title, update.message.audio.performer, update.message.caption)
                m.path, m.mime = self._download_file(update.message, update.message.audio, m.type)
            elif mtype == TGMsgType.Voice:
                m.type = MsgType.Audio
                m.text = update.message.caption
                m.path, m.mime = self._download_file(update.message, update.message.voice, m.type)
            elif mtype == TGMsgType.Location:
                m.type = MsgType.Location
                m.text = "Location"
                m.attributes = {
                    "latitude": update.message.location.latitude,
                    "longitude": update.message.location.longitude
                }
            elif mtype == TGMsgType.Venue:
                m.type = MsgType.Location
                m.text = update.message.location.title + "\n" + update.message.location.adderss
                m.attributes = {
                    "latitude": update.message.venue.location.latitude,
                    "longitude": update.message.venue.location.longitude
                }
            else:
                return self._reply_error(bot, update, "Message type not supported. (MN02)")

            slave_msg = self.slaves[channel].send_message(m)
        except EFBChatNotFound:
            self._reply_error(bot, update, "Chat is not reachable from the slave channel. (CN01)")
        except EFBMessageTypeNotSupported:
            self._reply_error(bot, update, "Message type not supported. (MN01)")
        except EFBMessageError as e:
            self._reply_error(bot, update, "Message is not sent. (MN01)\n\n%s" % str(e))
        else:
            msg_log_d = {
                "master_msg_id": "%s.%s" % (update.message.chat_id, update.message.message_id),
                "text": m.text or "Sent a %s" % m.type,
                "slave_origin_uid": "%s.%s" % (m.destination['channel'], m.destination['uid']),
                "slave_origin_display_name": "__chat__",
                "msg_type": m.type,
                "sent_to": "slave",
                "slave_message_id": "__fail__"
            }
            if slave_msg:
                msg_log_d['slave_message_id'] = slave_msg.uid
            db.add_msg_log(**msg_log_d)

    def _download_file(self, tg_msg, file_obj, msg_type):
        """
        Download media file from telegram platform.

        Args:
            tg_msg: Telegram message instance
            file_obj: File object
            msg_type: Type of message

        Returns:
            tuple of str[2]: Full path of the file, MIME type
        """
        path = os.path.join("storage", self.channel_id)
        if not os.path.exists(path):
            os.makedirs(path)
        size = getattr(file_obj, "file_size", None)
        file_id = file_obj.file_id
        if size and size > telegram.constants.MAX_FILESIZE_DOWNLOAD:
            raise EFBMessageError("Attachment is too large. Maximum 20 MB. (AT01)")
        f = self.bot.bot.getFile(file_id)
        fname = "%s_%s_%s_%s" % (msg_type, tg_msg.chat.id, tg_msg.message_id, int(time.time()))
        fullpath = os.path.join(path, fname)
        f.download(fullpath)
        mime = getattr(file_obj, "mime_type", magic.from_file(fullpath, mime=True))
        if type(mime) is bytes:
            mime = mime.decode()
        guess_ext = mimetypes.guess_extension(mime) or ".unknown"
        if guess_ext == ".unknown":
            self.logger.warning("File %s with mime %s has no matching extensions.", fullpath, mime)
        ext = ".jpeg" if mime == "image/jpeg" else guess_ext
        os.rename(fullpath, "%s%s" % (fullpath, ext))
        fullpath = "%s%s" % (fullpath, ext)
        return fullpath, mime

    def _download_gif(self, tg_msg, file_id, msg_type):
        """
        Download and convert GIF image.

        Args:
            tg_msg: Telegram message instance
            file_id: File ID
            msg_type: Type of message

        Returns:
            tuple of str[2]: Full path of the file, MIME type
        """
        fullpath, mime = self._download_file(tg_msg, file_id, msg_type)
        VideoFileClip(fullpath).write_gif(fullpath + ".gif", program="ffmpeg")
        return fullpath + ".gif", "image/gif"

    def start(self, bot, update, args=[]):
        """
        Process bot command `/start`.

        Args:
            bot: Telegram Bot instance
            update: Message update
            args: Arguments from message
        """
        if update.message.from_user.id != update.message.chat.id:  # from group
            try:
                data = self.msg_storage[self.b64de(args[0])]
            except KeyError:
                return update.message.reply_text("Session expired or unknown parameter. (SE02)")
            chat_uid = data["chat_uid"]
            chat_display_name = data["chat_display_name"]
            slave_channel, slave_chat_uid = chat_uid.split('.', 1)
            if slave_channel in self.slaves:
                if self.MUTE_CHAT_ID in db.get_chat_assoc(slave_uid=chat_uid):
                    db.remove_chat_assoc(slave_uid=chat_uid)
                db.add_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id),
                                  slave_uid=chat_uid,
                                  multiple_slave=self._flag("multiple_slave_chats", True))
                txt = "Chat '%s' is now linked." % chat_display_name
                unlink_btn = telegram.InlineKeyboardMarkup(
                    [[telegram.InlineKeyboardButton("Unlink", callback_data="unlink 0")]])
                new_msg = bot.send_message(update.message.chat.id, text=txt, reply_markup=unlink_btn)
                self.msg_status[args[0]] = \
                    self.msg_status["%s.%s" % (update.message.chat.id, new_msg.message_id)] = \
                    Flags.EXEC_LINK
                self.msg_storage[args[0]] = \
                    self.msg_storage["%s.%s" % (update.message.chat.id, new_msg.message_id)] = \
                    {"chats": data['chats']}
                bot.editMessageText(chat_id=data["tg_chat_id"],
                                    message_id=data["tg_msg_id"],
                                    text=txt,
                                    reply_markup=unlink_btn)
                self.msg_status.pop(args[0], False)
        else:
            txt = "Welcome to EH Forwarder Bot: EFB Telegram Master Channel.\n\n" \
                  "To learn more, please visit https://github.com/blueset/ehForwarderBot ."
            bot.send_message(update.message.from_user.id, txt)

    def help(self, bot, update):
        txt = "EFB Telegram Master Channel\n" \
              "/link\n" \
              "    Link a remote chat to an empty Telegram group.\n" \
              "    Followed by a regular expression to filter results.\n" \
              "/chat\n" \
              "    Generate a chat head to start a conversation.\n" \
              "    Followed by a regular expression to filter results.\n" \
              "/extra\n" \
              "    List all extra function from slave channels.\n" \
              "/unlink_all\n" \
              "    Unlink all remote chats in this chat.\n" \
              "/recog\n" \
              "    Reply to a voice message to convert it to text.\n" \
              "    Followed by a language code to choose a specific language.\n" \
              "    You have to enable speech to text in the config file first.\n" \
              "/help\n" \
              "    Print this command list."
        bot.send_message(update.message.from_user.id, txt)

    def recognize_speech(self, bot, update, args=[]):
        """
        Recognise voice message. Triggered by `/recog`.

        Args:
            bot: Telegram Bot instance
            update: Message update
            args: Arguments from message
        """

        class speechNotImplemented:
            lang_list = []

            def __init__(self, *args, **kwargs):
                pass

            def recognize(self, *args, **kwargs):
                return ["Not enabled or error in configuration."]

        if not getattr(update.message, "reply_to_message", None):
            txt = "/recog [lang_code]\nReply to a voice with this command to recognize it.\n" \
                  "mples:\n/recog\n/recog zh\n/recog en\n(RS01)"
            return self._reply_error(bot, update, txt)
        if not getattr(update.message.reply_to_message, "voice"):
            return self._reply_error(bot, update,
                                     "Reply only to a voice with this command to recognize it. (RS02)")
        try:
            baidu_speech = speech.BaiduSpeech(getattr(config, self.channel_id)['baidu_speech_api'])
        except:
            baidu_speech = speechNotImplemented()
        try:
            bing_speech = speech.BingSpeech(getattr(config, self.channel_id)['bing_speech_api'])
        except:
            bing_speech = speechNotImplemented()
        if len(args) > 0 and (args[0][:2] not in ['zh', 'en', 'ja'] and args[0] not in bing_speech.lang_list):
            return self._reply_error(bot, update, "Language is not supported. Try with zh, ja or en. (RS03)")
        if update.message.reply_to_message.voice.duration > 60:
            return self._reply_error(bot, update, "Only voice shorter than 60s is supported. (RS04)")
        path, mime = self._download_file(update.message, update.message.reply_to_message.voice, MsgType.Audio)

        results = {}
        if len(args) == 0:
            results['Baidu (English)'] = baidu_speech.recognize(path, "en")
            results['Baidu (Mandarin)'] = baidu_speech.recognize(path, "zh")
            results['Bing (English)'] = bing_speech.recognize(path, "en-US")
            results['Bing (Mandarin)'] = bing_speech.recognize(path, "zh-CN")
            results['Bing (Japanese)'] = bing_speech.recognize(path, "ja-JP")
        elif args[0][:2] == 'zh':
            results['Baidu (Mandarin)'] = baidu_speech.recognize(path, "zh")
            if args[0] in bing_speech.lang_list:
                results['Bing (%s)' % args[0]] = bing_speech.recognize(path, args[0])
            else:
                results['Bing (Mandarin)'] = bing_speech.recognize(path, "zh-CN")
        elif args[0][:2] == 'en':
            results['Baidu (English)'] = baidu_speech.recognize(path, "en")
            if args[0] in bing_speech.lang_list:
                results['Bing (%s)' % args[0]] = bing_speech.recognize(path, args[0])
            else:
                results['Bing (English)'] = bing_speech.recognize(path, "en-US")
        elif args[0][:2] == 'ja':
            results['Bing (Japanese)'] = bing_speech.recognize(path, "ja-JP")
        elif args[0][:2] == 'ct':
            results['Baidu (Cantonese)'] = baidu_speech.recognize(path, "ct")
        elif args[0] in bing_speech.lang_list:
            results['Bing (%s)' % args[0]] = bing_speech.recognize(path, args[0])

        msg = ""
        for i in results:
            msg += "\n*%s*:\n" % i
            for j in results[i]:
                msg += "%s\n" % j
        msg = "Results:\n%s" % msg
        bot.send_message(update.message.reply_to_message.chat.id, msg,
                        reply_to_message_id=update.message.reply_to_message.message_id,
                        parse_mode=telegram.ParseMode.MARKDOWN)
        os.remove(path)

    def poll(self):
        """
        Message polling process.
        """
        self.polling_from_tg()
        while True:
            try:
                m = self.queue.get()
                if m is None:
                    break
                self.logger.info("Got message from queue\nType: %s\nText: %s\n----" % (m.type, m.text))
                threading.Thread(target=self.process_msg, args=(m,)).start()
                self.queue.task_done()
                self.logger.info("Msg sent to TG, task_done marked.")
            except Exception as e:
                self.logger.error("Error occurred during message polling")
                self.logger.error(repr(e))
                self.bot.stop()
                self.poll()

        self.logger.debug("Gracefully stopping %s (%s).", self.channel_name, self.channel_id)
        self.bot.stop()
        self.logger.debug("%s (%s) gracefully stopped.", self.channel_name, self.channel_id)

    def polling_from_tg(self):
        """
        Poll message from Telegram Bot API. Can be used to extend for webhook.
        This method must NOT be blocking.
        """
        self.bot.start_polling(timeout=10)

    def error(self, bot, update, error):
        """
        Print error to console, and send error message to first admin.
        Triggered by python-telegram-bot error callback.
        """
        if "Conflict: terminated by other long poll or webhook (409)" in str(error):
            msg = 'Please immediately turn off this EFB instances.\nAnother bot instance or webhook detected.'
            self.logger.critical(msg)
            bot.send_message(getattr(config, self.channel_id)['admins'][0], msg)
            return
        try:
            raise error
        except telegram.error.Unauthorized:
            self.logger.error("The bot is not authorised to send update:\n%s\n%s", str(update), str(error))
        except telegram.error.BadRequest:
            self.logger.error("Message request is invalid.\n%s\n%s", str(update), str(error))
            bot.send_message(getattr(config, self.channel_id)['admins'][0],
                             "Message request is invalid.\n%s\n<code>%s</code>)" %
                             (html.escape(str(error)), html.escape(str(update))), parse_mode="HTML")
        except telegram.error.TimedOut:
            self.timeout_count += 1
            self.logger.error("Poor internet connection detected.\nError count: %s\n\%s\nUpdate: %s",
                              self.timeout_count, str(error), str(update))
            if update is not None and isinstance(getattr(update, "message", None), telegram.Message):
                update.message.reply_text("This message is not processed due to poor internet environment "
                                          "of the server.\n"
                                          "<code>%s</code>" % html.escape(str(error)), quote=True, parse_mode="HTML")
            if self.timeout_count >= 10:
                bot.send_message(getattr(config, self.channel_id)['admins'][0],
                                 "<b>EFB Telegram Master channel</b>\n"
                                 "You may have a poor internet connection on your server. "
                                 "Currently %s time-out errors are detected.\n"
                                 "For more details, please refer to the log." % (self.timeout_count),
                                 parse_mode="HTML")
        except telegram.error.ChatMigrated as e:
            new_id = e.new_chat_id
            old_id = update.message.chat_id
            count = 0
            for i in db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, old_id)):
                db.remove_chat_assoc(slave_uid=i)
                db.add_chat_assoc(master_uid="%s.%s" % (self.channel_id, new_id), slave_uid=i)
                count += 1
            bot.send_message(new_id, "Chat migration detected."
                                     "All remote chats (%s) are now linked to this new group." % count)
        except:
            try:
                bot.send_message(getattr(config, self.channel_id)['admins'][0],
                                 "EFB Telegram Master channel encountered error <code>%s</code> "
                                 "caused by update <code>%s</code>.\n\n"
                                 "Report issue: <a href=\"https://github.com/blueset/ehForwarderBot/issues/new\">GitHub Issue Page</a>" %
                                 (html.escape(str(error)), html.escape(str(update))), parse_mode="HTML")
            except:
                try:
                    bot.send_message(getattr(config, self.channel_id)['admins'][0],
                                     "EFB Telegram Master channel encountered error\n%s\n"
                                     "caused by update\n%s\n\n"
                                     "Report issue: https://github.com/blueset/ehForwarderBot/issues/new" %
                                     (html.escape(str(error)), html.escape(str(update))))
                except:
                    self.logger.error("Failed to send error message.")
            self.logger.error('Unhandled telegram bot error!\n'
                              'Update %s caused error %s' % (update, error))

    def _flag(self, key, value):
        """
        Retrieve value for experimental flags.

        Args:
            key: Key of the flag.
            value: Default/fallback value.

        Returns:
            Value for the flag.
        """
        return getattr(config, self.channel_id).get('flags', dict()).get(key, value)

    @property
    def stop_polling(self):
        return self._stop_polling

    @stop_polling.setter
    def stop_polling(self, val):
        if val:
            self.queue.put(None)
        self._stop_polling = val

    @staticmethod
    def b64en(s):
        return base64.b64encode(s.encode(), b"-_").decode().rstrip("=")

    @staticmethod
    def b64de(s):
        return base64.b64decode((s + '=' * (- len(s) % 4)).encode(), b"-_").decode()
