import telegram
import telegram.ext
import config
import utils
import urllib
from . import db
from .whitelisthandler import WhitelistHandler
from channel import EFBChannel, EFBMsg, MsgType, MsgSource, TargetType, ChannelType


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

        self.me = self.bot.get_me()
        self.bot.dispatcher.add_handler(WhitelistHandler(config.eh_telegram_master['admins']))
        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("link", self.link_chat_show_list))
        self.bot.dispatcher.add_handler(telegram.ext.CallbackQueryHandler(self.callback_query_dispatcher))

    def callback_query_dispatcher(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        text = query.data
        msg_id = update.inline_message_id
        msg_status = self.msg_status[msg_id]
        if msg_status in [Flags.CONFIRM_LINK]:
            self.link_chat_confirm(bot, chat_id, msg_id, msg_status)
        else:
            bot.editMessageText(text="Session expired. Please try again.",
                                chat_id=chat_id,
                                message_id=msg_id)

    def process_msg(self, msg):
        pass

    def link_chat_show_list(self, bot, update):
        user_id = update.message.from_user.id
        # if update.chat_id != bot.me.id:
        #     init_msg = bot.send("processing")
        #     cid = db.get_chat_assoc(master_cid=update.chat_id).slave_cid
        #     return self.link_chat_confirm_list(msg_id, msg_id=init_msg.id, chat_id=cid)

        # if update.reply_to:
        #     init_msg = bot.send("processing")
        #     cid = db.get_chat_log(replyto.id).chat_id
        #     retrun self.link_chat_confirm_list(msg_id, msg_id=init_msg.id, chat_id=cid)
        legend = [
            "%s: Linked" % utils.Emojis.LINK_EMOJI,
            "%s: User" % utils.Emojis.USER_EMOJI,
            "%s: Group" % utils.Emojis.GROUP_EMOJI,
            "%s: System" % utils.Emojis.SYSTEM_EMOJI,
            "%s: Unknown" % utils.Emojis.UNKNOWN_EMOJI
        ]
        chat_btn_list = []
        for slave in self.slaves:
            slave_chats = slave.get_chats()
            slave_id = slave.channel_id
            slave_name = slave.channel_name
            slave_emoji = slave.channel_emoji
            legend.append("%s: %s" % (slave_emoji, slave_name))
            for chat in slave_chats:
                uid = "%s.%s" % (slave_id, chat['uid'])
                linked = utils.Emojis.LINK_EMOJI if bool(db.get_chat_assoc(slave_id=uid)) else ""
                chat_type = utils.Emojis.get_type_emoji(chat['type'])
                chat_name = chat['alias'] if chat['name'] == chat['alias'] else "%s(%s)" % (chat['alias'], chat['name'])
                button_text = "%s%s: %s%s" % (slave_emoji, chat_type, chat_name, linked)
                chat_btn_list.append(
                    [telegram.InlineKeyboardButton(button_text, callback_data="%s\x1f%s" % (uid, button_text))])
        chat_btn_list.append([telegram.sInlineKeyboardButton("Cancel", callback_data=Flags.CANCEL_PROCESS)])
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
        self.msg_status[tg_msg_id] = Flags.EXEC_LINK
        chat_uid, button_txt = callback_uid.split('\x1f', 1)
        linked = bool(db.get_chat_assoc(slave_id=chat_uid))
        txt = "You've selected chat '%s'."
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

    def poll(self):
        self.bot.start_polling(network_delay=5)
        while True:
            if not self.queue.empty():
                m = self.queue.get()
                self.process_msg(m)
