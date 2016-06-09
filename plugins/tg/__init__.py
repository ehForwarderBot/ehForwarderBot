import telegram
import telegram.ext
import config
import utils
import urllib
import logging
from . import db
from .whitelisthandler import WhitelistHandler
from channel import EFBChannel, EFBMsg, MsgType, MsgSource, TargetType, ChannelType
from channelExceptions import EFBChatNotFound
from .msgType import get_msg_type, TGMsgType

class Flags:
    # General Flags
    CANCEL_PROCESS = "cancel"
    # Chat linking
    CONFIRM_LINK = 0x11
    EXEC_LINK = 0x12
    pass


class TelegramChannel(EFBChannel):
    """
    EFB Channel - Telegram (Master)
    Requires python-telegram-bot

    Author: Eana Hufwe <https://github.com/blueset>

    Additional configs:
    eh_telegram_master = {
        "token": "123456789:1A2b3C4D5e6F7G8H9i0J1k2L3m4N5o6P7q8",
        "admins": [12345678, 87654321]
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
        self.bot.dispatcher.add_handler(telegram.ext.CallbackQueryHandler(self.callback_query_dispatcher))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("start", self.start, pass_args=True))
        self.bot.dispatcher.add_handler(telegram.ext.RegexHandler('.*', self.msg))
        self.bot.dispatcher.add_error_handler(self.error)

    def callback_query_dispatcher(self, bot, update):
        # Get essential information about the query
        query = update.callback_query
        chat_id = query.message.chat.id
        user_id = query.from_user.id
        text = query.data
        msg_id = update.callback_query.message.message_id
        msg_status = self.msg_status.get(msg_id, None)

        # dispatch the query
        if msg_status in [Flags.CONFIRM_LINK]:
            self.link_chat_confirm(bot, chat_id, msg_id, text)
        elif msg_status in [Flags.EXEC_LINK]:
            self.link_chat_exec(bot, chat_id, msg_id, text)
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
        if not msg.source == MsgSource.Group:
            msg.member = {"uid": -1, "name": "", "alias": ""}
        if msg.type == MsgType.Text:
            if msg.source == MsgSource.Group:
                msg_prefix = msg.member['alias'] if msg.member['name'] == msg.member['alias'] else "$s (%s)" % (msg.member['name'], msg.member['alias'])
            if tg_chat:  # if this chat is linked
                tg_dest = int(tg_chat.split('.')[1])
                if msg_prefix:  # if group message
                    txt = "%s:\n%s" % (msg_prefix, msg.text)
                else:
                    txt = msg.text
            else:  # when chat is not linked
                tg_dest = config.eh_telegram_master['admins'][0]
                emoji_prefix = msg.channel_emoji + utils.Emojis.get_source_emoji(msg.source)
                name_prefix = msg.destination["alias"] if msg.destination["alias"] == msg.destination["name"] else "%s (%s)" % (msg.destination["alias"], msg.destination["name"])
                if msg_prefix:
                    txt = "%s %s [%s]:\n%s" % (emoji_prefix, msg_prefix, name_prefix, msg.text)
                else:
                    txt = "%s %s:\n%s" % (emoji_prefix, name_prefix, msg.text)
            tg_msg=self.bot.bot.sendMessage(tg_dest, text=txt)
        db.add_msg_log(master_msg_id="%s.%s" % (tg_msg.chat.id, tg_msg.message_id),
                       text=tg_msg.text,
                       slave_origin_uid="%s.%s" % (msg.channel_id, msg.origin['uid']),
                       msg_type=msg.type,
                       sent_to="Master",
                       slave_origin_display_name=msg.origin['alias'],
                       slave_member_uid=msg.member['uid'],
                       slave_member_display_name=msg.member['alias'])

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
                chat_btn_list.append(
                    [telegram.InlineKeyboardButton(button_text, callback_data="%s\x1f%s" % (uid, button_text))])
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

    def msg(self, bot, update):
        target = None
        if not (update.message.chat.id == update.message.from_user.id):  # from group
            assoc = db.get_chat_assoc(master_uid="%s.%s" % (self.channel_id, update.message.chat.id))
            if getattr(update.message, "reply_to_message", None):
                target = db.get_msg_log("%s.%s" % (update.message.reply_to_message.chat.id, update.message.reply_to_message.message_id)).slave_origin_uid
                targetChannel, targetUid = target.split('.', 2)
        elif (update.message.chat.id == update.message.from_user.id) and hasattr(update.message, "reply_to_message"):  # reply to user
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
                if targetChannel is channel:
                    m.target = {"uid": uid, 'name': '', 'alias': ''}
            # Type specific stuff
            if mtype is TGMsgType.Text:
                m.type = MsgType.Text
                m.text = update.message.text
                print("m.text", m.text, update.message.text)

            self.slaves[channel].send_message(m)
        except EFBChatNotFound:
            return self._reply_error(bot, update, "Internal error: Chat not found in channel.")

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
