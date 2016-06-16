import telegram
import telegram.ext
import config
import utils
import urllib
import logging
import time
import magic
import os
import mimetypes
import pydub
from . import db, speech
from .whitelisthandler import WhitelistHandler
from channel import EFBChannel, EFBMsg, MsgType, MsgSource, TargetType, ChannelType
from channelExceptions import EFBChatNotFound, EFBMessageTypeNotSupported
from .msgType import get_msg_type, TGMsgType


class Flags:
    # General Flags
    CANCEL_PROCESS = "cancel"
    # Chat linking
    CONFIRM_LINK = 0x11
    EXEC_LINK = 0x12
    # Start a chat
    START_CHOOSE_CHAT = 0x21
    pass


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

    # Meta Info
    channel_name = "Telegram Master"
    channel_emoji = "✈"
    channel_id = "eh_telegram_master"
    channel_type = ChannelType.Master

    # Data
    slaves = None
    bot = None
    msg_status = {}
    me = None

    def __init__(self, queue, slaves):
        super().__init__(queue)
        self.slaves = slaves
        try:
            self.bot = telegram.ext.Updater(config.eh_telegram_master['token'])
        except (AttributeError, KeyError):
            raise NameError("Token is not properly defined. Please define it in `config.py`.")

        self.logger = logging.getLogger("masterTG.%s" % __name__)
        self.me = self.bot.bot.get_me()
        self.bot.dispatcher.add_handler(WhitelistHandler(config.eh_telegram_master['admins']))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("link", self.link_chat_show_list))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("chat", self.start_chat_list))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("recog", self.recognize_speech, pass_args=True))
        self.bot.dispatcher.add_handler(telegram.ext.CallbackQueryHandler(self.callback_query_dispatcher))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("start", self.start, pass_args=True))
        self.bot.dispatcher.add_handler(telegram.ext.MessageHandler(
            [telegram.ext.Filters.text,
             telegram.ext.Filters.photo,
             telegram.ext.Filters.sticker,
             telegram.ext.Filters.document],
            self.msg
        ))
        self.bot.dispatcher.add_error_handler(self.error)

    def callback_query_dispatcher(self, bot, update):
        # Get essential information about the query
        query = update.callback_query
        chat_id = query.message.chat.id
        text = query.data
        msg_id = update.callback_query.message.message_id
        msg_status = self.msg_status.get(msg_id, None)

        # dispatch the query
        if msg_status in [Flags.CONFIRM_LINK]:
            self.link_chat_confirm(bot, chat_id, msg_id, text)
        elif msg_status in [Flags.EXEC_LINK]:
            self.link_chat_exec(bot, chat_id, msg_id, text)
        elif msg_status == Flags.START_CHOOSE_CHAT:
            self.make_chat_head(bot, chat_id, msg_id, text)
        else:
            bot.editMessageText(text="Session expired. Please try again.",
                                chat_id=chat_id,
                                message_id=msg_id)

    def _reply_error(self, bot, update, errmsg):
        return bot.sendMessage(update.message.chat.id, errmsg, reply_to_message_id=update.message.message_id)

    def process_msg(self, msg):
        chat_uid = "%s.%s" % (msg.channel_id, msg.origin['uid'])
        tg_chat = db.get_chat_assoc(slave_uid=chat_uid) or False
        msg_prefix = ""
        tg_msg = None
        tg_chat_assoced = False
        is_last_member = False
        if not msg.source == MsgSource.Group:
            msg.member = {"uid": -1, "name": "", "alias": ""}

        # Generate chat text template & Decide type target

        if msg.source == MsgSource.Group:
            msg_prefix = msg.member['alias'] if msg.member['name'] == msg.member['alias'] else "%s (%s)" % (msg.member['alias'], msg.member['name'])
        if tg_chat:  # if this chat is linked
            tg_dest = int(tg_chat.split('.')[1])
            tg_chat_assoced = True
            if msg_prefix:  # if group message
                msg_template = "%s:\n%s" % (msg_prefix, "%s")
            else:
                msg_template = "%s"
        else:  # when chat is not linked
            tg_dest = config.eh_telegram_master['admins'][0]
            emoji_prefix = msg.channel_emoji + utils.Emojis.get_source_emoji(msg.source)
            name_prefix = msg.origin["alias"] if msg.origin["alias"] == msg.origin["name"] else "%s (%s)" % (msg.origin["alias"], msg.origin["name"])
            if msg_prefix:
                msg_template = "%s %s [%s]:\n%s" % (emoji_prefix, msg_prefix, name_prefix, "%s")
            else:
                msg_template = "%s %s:\n%s" % (emoji_prefix, name_prefix, "%s")

        # Type dispatching

        if msg.type in [MsgType.Text, MsgType.Link]:
            last_msg = db.get_last_msg_from_chat(tg_dest)
            if last_msg:
                if last_msg.msg_type == "Text":
                    if msg.source == MsgSource.Group:
                        is_last_member = str(last_msg.slave_member_uid) == str(msg.member['uid'])
                    else:
                        is_last_member = str(last_msg.slave_origin_uid) == "%s.%s" % (msg.channel_id, msg.origin['uid'])
                else:
                    is_last_member = False
            else:
                is_last_member = False
            if tg_chat_assoced and is_last_member:
                msg.text = "%s\n%s" % (last_msg.text, msg.text)
                tg_msg = self.bot.bot.editMessageText(chat_id=tg_dest, 
                    message_id=last_msg.master_msg_id.split(".", 2)[1],
                    text=msg_template % msg.text)
            else:
                tg_msg = self.bot.bot.sendMessage(tg_dest, text=msg_template % msg.text)
        elif msg.type in [MsgType.Image, MsgType.Sticker]:
            self.logger.info("recieved Image/Sticker \nPath: %s\nSize: %s\nMIME: %s", msg.path, os.stat(msg.path).st_size, msg.mime)
            if os.stat(msg.path).st_size == 0:
                os.remove(msg.path)
                return self.bot.bot.sendMessage(tg_dest, msg_template % ("Error: Empty %s recieved" % msg.type))
            if not msg.text:
                if msg.type == MsgType.Image:
                    msg.text = "sent a picture."
                elif msg.type == MsgType.Sticker:
                    msg.text = "sent a sticker."
            if msg.mime == "image/gif":
                tg_msg = self.bot.bot.sendDocument(tg_dest, msg.file, caption=msg_template % msg.text)
            else:
                tg_msg = self.bot.bot.sendPhoto(tg_dest, msg.file, caption=msg_template % msg.text)
            os.remove(msg.path)
        elif msg.type == MsgType.File:
            if os.stat(msg.path).st_size == 0:
                os.remove(msg.path)
                return self.bot.bot.sendMessage(tg_dest, msg_template % ("Error: Empty %s recieved" % msg.type))
            if not msg.text:
                file_name = os.path.basename(msg.path)
                msg.text = "sent a file."
            else:
                file_name = msg.text
            tg_msg = self.bot.bot.sendDocument(tg_dest, msg.file, caption=msg_template % msg.text, filename=file_name)
            os.remove(msg.path)
        elif msg.type == MsgType.Audio:
            if os.stat(msg.path).st_size == 0:
                os.remove(msg.path)
                return self.bot.bot.sendMessage(tg_dest, msg_template % ("Error: Empty %s recieved" % msg.type))
            pydub.AudioSegment.from_file(msg.file).export("%s.ogg" % msg.path, format="ogg", codec="libopus")
            ogg_file = open("%s.ogg" % msg.path, 'rb')
            if not msg.text:
                msg.text = "🔉"
            tg_msg = self.bot.bot.sendMessage(tg_dest, text=msg_template % msg.text)
            os.remove(msg.path)
            os.remove("%s.ogg" % msg.path)
            self.bot.bot.sendVoice(tg_dest, ogg_file, reply_to_message_id=tg_msg.message_id)
        elif msg.type == MsgType.Location:
            tg_msg = self.bot.bot.sendVenue(tg_dest, latitude=msg.attributes['latitude'], longitude=msg.attributes['longitude'], title=msg.text, address=msg_template % "")
        elif msg.type == MsgType.Video:
            if os.stat(msg.path).st_size == 0:
                os.remove(msg.path)
                return self.bot.bot.sendMessage(tg_dest, msg_template % ("Error: Empty %s recieved" % msg.type))
            if not msg.text:
                msg.text = "sent a video."
            tg_msg = self.bot.bot.sendVideo(tg_dest, video=msg.file, caption=msg_template % msg.text)
            os.remove(msg.path)
        else:
            tg_msg = self.bot.bot.sendMessage(tg_dest, msg_template % "Unsupported incoming message type. (UT01)")
        msg_log = {"master_msg_id": "%s.%s" % (tg_msg.chat.id, tg_msg.message_id),
                   "text": msg.text,
                   "msg_type": msg.type,
                   "sent_to": "Master",
                   "slave_origin_uid": "%s.%s" % (msg.channel_id, msg.origin['uid']),
                   "slave_origin_display_name": msg.origin['alias'],
                   "slave_member_uid": msg.member['uid'],
                   "slave_member_display_name": msg.member['alias']}
        if tg_chat_assoced and is_last_member:
            msg_log['update'] = True
        db.add_msg_log(**msg_log)

    def link_chat_show_list(self, bot, update):
        user_id = update.message.from_user.id
        # if message sent from a group
        if not update.message.chat.id == update.message.from_user.id:
            init_msg = bot.sendMessage(self.me.id, "Processing...")
            try:
                cid = db.get_chat_assoc(update.message.chat.id).slave_cid
                return self.link_chat_confirm(bot, init_msg.fsom_chat.id, init_msg.message_id, cid)
            except:
                return bot.editMessageText(chat_id=update.message.chat.id,
                                           message_id=init_msg.message_id,
                                           text="No chat is found linked with this group. Please send /link privately to link a chat.")

        # if message ir replied to an existing one
        if update.message.reply_to_message:
            init_msg = bot.sendMessage(self.me.id, "Processing...")
            try:
                cid = db.get_chat_log(update.message.reply_to_message.message_id).slave_origin_uid
                return self.link_chat_confirm(bot, init_msg.fsom_chat.id, init_msg.message_id, cid)
            except:
                return bot.editMessageText(chat_id=update.message.chat.id,
                                           message_id=init_msg.message_id,
                                           text="No chat is found linked with this group. Please send /link privately to link a chat.")
        legend = [
            "%s: Linked" % utils.Emojis.LINK_EMOJI,
            "%s: User" % utils.Emojis.USER_EMOJI,
            "%s: Group" % utils.Emojis.GROUP_EMOJI,
            "%s: System" % utils.Emojis.SYSTEM_EMOJI,
            "%s: Unknown" % utils.Emojis.UNKNOWN_EMOJI
        ]
        chat_btn_list = []
        for slave_id in self.slaves:
            slave = self.slaves[slave_id]
            slave_chats = slave.get_chats()
            # slave_id = slave.channel_id
            slave_name = slave.channel_name
            slave_emoji = slave.channel_emoji
            legend.append("%s: %s" % (slave_emoji, slave_name))
            for chat in slave_chats:
                uid = "%s.%s" % (slave_id, chat['uid'])
                linked = utils.Emojis.LINK_EMOJI if bool(db.get_chat_assoc(slave_uid=uid)) else ""
                chat_type = utils.Emojis.get_source_emoji(chat['type'])
                chat_name = chat['alias'] if chat['name'] == chat['alias'] else "%s(%s)" % (chat['alias'], chat['name'])
                button_text = "%s%s: %s%s" % (slave_emoji, chat_type, chat_name, linked)
                button_callback = "%s\x1f%s" % (uid, chat_name)
                chat_btn_list.append(
                    [telegram.InlineKeyboardButton(button_text, callback_data=button_callback[:32])])
        chat_btn_list.append([telegram.InlineKeyboardButton("Cancel", callback_data=Flags.CANCEL_PROCESS)])
        msg_text = "Please choose the chat you want to link with ...\n\nLegend:\n"
        for i in legend:
            msg_text += "%s\n" % i
        msg = bot.sendMessage(user_id, text=msg_text, reply_markup=telegram.InlineKeyboardMarkup(chat_btn_list))
        self.msg_status[msg.message_id] = Flags.CONFIRM_LINK

    def link_chat_confirm(self, bot, tg_chat_id, tg_msg_id, callback_uid):
        if callback_uid == Flags.CANCEL_PROCESS:
            txt = "Cancelled."
            self.msg_status.pop(tg_msg_id, None)
            return bot.editMessageText(text=txt,
                                       chat_id=tg_chat_id,
                                       message_id=tg_msg_id)
        chat_uid, button_txt = callback_uid.split('\x1f', 1)
        linked = bool(db.get_chat_assoc(slave_uid=chat_uid))
        self.msg_status[tg_msg_id] = Flags.EXEC_LINK
        self.msg_status[chat_uid] = tg_msg_id
        txt = "You've selected chat '%s'." % button_txt
        if linked:
            txt += "\nThis chat has already linked to Telegram."
        txt += "\nWhat would you like to do?"

        if linked:
            btn_list = [telegram.InlineKeyboardButton("Relink", url="https://telegram.me/%s?startgroup=%s" % (self.me.username, urllib.parse.quote(chat_uid))),
                        telegram.InlineKeyboardButton("Unlink", callback_data="%s\x1fUnlink" % callback_uid)]
        else:
            btn_list = [telegram.InlineKeyboardButton("Link", url="https://telegram.me/%s?startgroup=%s" % (self.me.username, urllib.parse.quote(chat_uid)))]
        btn_list.append(telegram.InlineKeyboardButton("Cancel", callback_data=Flags.CANCEL_PROCESS))

        bot.editMessageText(text=txt,
                            chat_id=tg_chat_id,
                            message_id=tg_msg_id,
                            reply_markup=telegram.InlineKeyboardMarkup([btn_list]))

    def link_chat_exec(self, bot, tg_chat_id, tg_msg_id, callback_uid):
        if callback_uid == Flags.CANCEL_PROCESS:
            txt = "Cancelled."
            self.msg_status.pop(tg_msg_id, None)
            return bot.editMessageText(text=txt,
                                       chat_id=tg_chat_id,
                                       message_id=tg_msg_id)
        chat_uid, button_txt, cmd = callback_uid.split('\x1f', 2)
        self.msg_status.pop(tg_msg_id, None)
        self.msg_status.pop(chat_uid, None)
        if cmd == "Unlink":
            db.remove_chat_assoc(slave_uid=chat_uid)
            txt = "Chat '%s' has been unlinked." % (button_txt)
            return bot.editMessageText(text=txt, chat_id=tg_chat_id, message_id=tg_msg_id)
        txt = "Command '%s' (%s) is not recognised, please try again" % (cmd, callback_uid)
        bot.editMessageText(text=txt, chat_id=tg_chat_id, message_id=tg_msg_id)

    def start_chat_list(self, bot, update):
        legend = [
            "%s: Linked" % utils.Emojis.LINK_EMOJI,
            "%s: User" % utils.Emojis.USER_EMOJI,
            "%s: Group" % utils.Emojis.GROUP_EMOJI,
            "%s: System" % utils.Emojis.SYSTEM_EMOJI,
            "%s: Unknown" % utils.Emojis.UNKNOWN_EMOJI
        ]
        chat_btn_list = []
        for slave_id in self.slaves:
            slave = self.slaves[slave_id]
            slave_chats = slave.get_chats()
            # slave_id = slave.channel_id
            slave_name = slave.channel_name
            slave_emoji = slave.channel_emoji
            legend.append("%s: %s" % (slave_emoji, slave_name))
            for chat in slave_chats:
                uid = "%s.%s" % (slave_id, chat['uid'])
                chat_type = utils.Emojis.get_source_emoji(chat['type'])
                chat_name = chat['alias'] if chat['name'] == chat['alias'] else "%s(%s)" % (chat['alias'], chat['name'])
                button_text = "%s%s: %s" % (slave_emoji, chat_type, chat_name)
                button_callback = "%s\x1f%s" % (uid, chat_name)
                chat_btn_list.append(
                    [telegram.InlineKeyboardButton(button_text, callback_data=button_callback[:32])])
        chat_btn_list.append([telegram.InlineKeyboardButton("Cancel", callback_data=Flags.CANCEL_PROCESS)])
        msg_text = "Choose a chat you want to start with...\n\nLegend:\n"
        for i in legend:
            msg_text += "%s\n" % i
        msg = bot.sendMessage(update.message.from_user.id, text=msg_text, reply_markup=telegram.InlineKeyboardMarkup(chat_btn_list))
        self.msg_status[msg.message_id] = Flags.START_CHOOSE_CHAT

    def make_chat_head(self, bot, tg_chat_id, tg_msg_id, callback_uid):
        if callback_uid == Flags.CANCEL_PROCESS:
            txt = "Cancelled."
            self.msg_status.pop(tg_msg_id, None)
            return bot.editMessageText(text=txt,
                                       chat_id=tg_chat_id,
                                       message_id=tg_msg_id)
        chat_uid, button_txt = callback_uid.split('\x1f', 1)
        self.msg_status.pop(tg_msg_id, None)
        self.msg_status.pop(chat_uid, None)
        msg_log = {"master_msg_id": "%s.%s" % (tg_chat_id, tg_msg_id),
                   "text": "",
                   "msg_type": "Text",
                   "sent_to": "Master",
                   "slave_origin_uid": chat_uid,
                   "slave_origin_display_name": button_txt,
                   "slave_member_uid": None,
                   "slave_member_display_name": None}
        db.add_msg_log(**msg_log)
        txt = "Reply to this message to chat with %s." % (button_txt)
        bot.editMessageText(text=txt, chat_id=tg_chat_id, message_id=tg_msg_id)

    def msg(self, bot, update):
        target = None
        if not (update.message.chat.id == update.message.from_user.id):  # from group
            assoc = db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id))
            if getattr(update.message, "reply_to_message", None):
                try:
                    targetlog = db.get_msg_log("%s.%s" % (update.message.reply_to_message.chat.id, update.message.reply_to_message.message_id))
                    target = targetlog.slave_origin_uid
                    targetChannel, targetUid = target.split('.', 2)
                except:
                    return self._reply_error(bot, update, "Unknown recipient (UC03).")
        elif (update.message.chat.id == update.message.from_user.id) and getattr(update.message, "reply_to_message", None):  # reply to user
            assoc = db.get_msg_log("%s.%s" % (update.message.reply_to_message.chat.id, update.message.reply_to_message.message_id)).slave_origin_uid
        else:
            return self._reply_error(bot, update, "Unknown recipient (UC01).")
        if not assoc:
            return self._reply_error(bot, update, "Unknown recipient (UC02).")
        channel, uid = assoc.split('.', 2)
        if channel not in self.slaves:
            return self._reply_error(bot, update, "Internal error: Channel not found.")
        try:
            m = EFBMsg(self)
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
                    trgtMsg.member = {
                        "name": targetlog.slave_member_display_name,
                        "alias": targetlog.slave_member_display_name,
                        "uid": targetlog.slave_member_uid
                    }
                    trgtMsg.origin = {
                        "name": targetlog.slave_origin_display_name,
                        "alias": targetlog.slave_origin_display_name,
                        "uid": targetlog.slave_origin_uid.split('.', 2)[1]
                    }
                    m.target = {
                        "type": TargetType.Message,
                        "target": trgtMsg
                    }
            # Type specific stuff
            if mtype == TGMsgType.Text:
                m.type = MsgType.Text
                m.text = update.message.text
            elif mtype == TGMsgType.Photo:
                m.type = MsgType.Image
                m.text = update.message.caption
                tg_file_id = update.message.photo[-1].file_id
                m.path, m.mime = self._download_file(update.message, tg_file_id, m.type)
                m.file = open(m.path, "rb")
            elif mtype == TGMsgType.Sticker:
                m.type = MsgType.Sticker
                m.text = update.message.sticker.emoji
                tg_file_id = update.message.sticker.file_id
                m.path, m.mime = self._download_file(update.message, tg_file_id, m.type)
                m.file = open(m.path, "rb")
            elif mtype == TGMsgType.Document:
                m.type = MsgType.File
                m.text = update.message.document.file_name
                tg_file_id = update.message.document.file_id
                m.path, m.mime = self._download_file(update.message, tg_file_id, m.type)
                m.file = open(m.path, "rb")
            else:
                return self._reply_error(bot, update, "Message type not supported. (MN02)")

            self.slaves[channel].send_message(m)
        except EFBChatNotFound:
            return self._reply_error(bot, update, "Internal error: Chat not found in channel. (CN01)")
        except EFBMessageTypeNotSupported:
            return self._reply_error(bot, update, "Message type not supported. (MN01)")

    def _download_file(self, tg_msg, file_id, msg_type):
        path = os.path.join("storage", self.channel_id)
        if not os.path.exists(path):
            os.makedirs(path)
        f = self.bot.bot.getFile(file_id)
        fname = "%s_%s_%s_%s" % (msg_type, tg_msg.chat.id, tg_msg.message_id, int(time.time()))
        fullpath = os.path.join(path, fname)
        f.download(fullpath)
        mime = magic.from_file(fullpath, mime=True).decode()
        ext = mimetypes.guess_extension(mime)
        os.rename(fullpath, "%s.%s" % (fullpath, ext))
        fullpath = "%s.%s" % (fullpath, ext)
        return fullpath, mime

    def start(self, bot, update, args=[]):
        if not update.message.from_user.id == update.message.chat.id:  # from group
            chat_uid = ' '.join(args)
            slave_channel, slave_chat_uid = chat_uid.split('.', 1)
            if slave_channel in self.slaves and chat_uid in self.msg_status:
                db.add_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id), slave_uid=chat_uid)
                txt = "Chat has been associated."
                bot.sendMessage(update.message.chat.id, text=txt)
                bot.editMessageText(chat_id=update.message.from_user.id,
                                    message_id=self.msg_status[chat_uid],
                                    text=txt)
                self.msg_status.pop(self.msg_status[chat_uid], False)
                self.msg_status.pop(chat_uid, False)
        elif update.message.from_user.id == update.message.chat.id and args == []:
            txt = "Welcome to EH Forwarder Bot.\n\nLearn more, please visit https://github.com/blueset/ehForwarderBot ."
            self.sendMessage(update.message.from_user.id, txt)

    def recognize_speech(self, bot, update, args=[]):
        class speechNotImplemented:
            lang_list = []

            def __init__(self, *args, **kwargs):
                pass

            def recognize(self, *args, **kwargs):
                return ["Not Implemented."]

        if not getattr(update.message, "reply_to_message", None):
            txt = "/recog [lang_code]\nReply to a voice with this command to recognised a voice.\nExamples:\n/recog\n/recog zh\n/recog en\n(RS01)"
            return self._reply_error(bot, update, txt)
        if not getattr(update.message.reply_to_message, "voice"):
            return self._reply_error(bot, update, "Reply only to a voice with this command to recognised a voice. (RS02)")
        try:
            baidu_speech = speech.BaiduSpeech(config.eh_telegram_master['baidu_speech_api'])
        except:
            baidu_speech = speechNotImplemented()
        try:
            bing_speech = speech.BingSpeech(config.eh_telegram_master['bing_speech_api'])
        except:
            bing_speech = speechNotImplemented()
        if len(args) > 0 and (args[0][:2] not in ['zh', 'en', 'ja'] and args[0] not in bing_speech.lang_list):
            return self._reply_error(bot, update, "Language is not supported. Try with zh, ja or en. (RS03)")
        if update.message.reply_to_message.voice.duration > 60:
            return self._reply_error(bot, update, "Only voice shorter than 60s is supported. (RS04)")
        path, mime = self._download_file(update.message, update.message.reply_to_message.voice.file_id, MsgType.Audio)

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
        bot.sendMessage(update.message.reply_to_message.chat.id, msg, reply_to_message_id=update.message.reply_to_message.message_id, parse_mode=telegram.ParseMode.MARKDOWN)
        os.remove(path)

    def poll(self):
        self.bot.start_polling(network_delay=5)
        while True:
            if not self.queue.empty():
                m = self.queue.get()
                self.logger.info("Got message from queue\nType: %s\nText: %s\n----" % (m.type, m.text))
                self.process_msg(m)

    def error(self, bot, update, error):
        """ Print error to console """
        self.logger.warn('ERRORRR! Update %s caused error %s' % (update, error))
        import pprint
        pprint.pprint(error)
